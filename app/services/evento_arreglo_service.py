from app.database.connection import get_connection

from app.services.eventos_service import (
    ESTATUS_EN_NEGOCIACION,
    actualizar_totales_evento,
    borrar_precio_acordado
)
from app.services.compras_service import (
    congelar_insumos_arreglo
)

def agregar_arreglo_evento(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT costo_total
        FROM arreglos
        WHERE id = %s
    """, (data.arreglo_id,))

    arreglo = cur.fetchone()

    if not arreglo:

        cur.close()
        conn.close()

        return {
            "error": "Arreglo no encontrado"
        }

    costo_unitario = float(arreglo[0])

    subtotal = (
        costo_unitario *
        data.cantidad
    )

    cur.execute("""
        INSERT INTO evento_arreglos (

            evento_id,
            arreglo_id,
            cantidad,
            costo_unitario,
            subtotal,
            observaciones

        )
        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,
            %s

        )
        RETURNING id
    """, (

        data.evento_id,
        data.arreglo_id,
        data.cantidad,
        costo_unitario,
        subtotal,
        data.observaciones

    ))

    nuevo_id = cur.fetchone()[0]

    # Foto de insumos (cantidades, factor, costo de paquete) en la misma
    # transacción: el renglón y su foto se guardan juntos o no se guardan.
    congelar_insumos_arreglo(cur, nuevo_id, data.arreglo_id)

    precio_borrado = borrar_precio_acordado(cur, data.evento_id)

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        data.evento_id
    )
    return {
        "mensaje": "Arreglo agregado",
        "id": nuevo_id,
        "precio_borrado": precio_borrado
    }


def obtener_arreglos_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            ea.id,

            ea.evento_id,

            ea.arreglo_id,

            a.codigo,

            a.nombre,

            ea.cantidad,

            ea.costo_unitario,

            ea.subtotal,

            ea.observaciones

        FROM evento_arreglos ea

        INNER JOIN arreglos a
            ON ea.arreglo_id = a.id

        WHERE ea.evento_id = %s

        ORDER BY ea.id
    """, (evento_id,))

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    cur.close()
    conn.close()

    return resultado

def editar_arreglo_evento(detalle_id, data):

    conn = get_connection()
    cur = conn.cursor()

    # Obtener datos actuales
    cur.execute("""
        SELECT
            evento_id,
            costo_unitario,
            cantidad
        FROM evento_arreglos
        WHERE id = %s
    """, (detalle_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Detalle no encontrado"
        }

    evento_id = fila[0]
    costo_unitario = float(fila[1])

    subtotal = (
        costo_unitario *
        data.cantidad
    )

    cur.execute("""
        UPDATE evento_arreglos
        SET
            cantidad = %s,
            subtotal = %s,
            observaciones = %s
        WHERE id = %s
    """, (

        data.cantidad,
        subtotal,
        data.observaciones,
        detalle_id

    ))

    # Cambiar solo las observaciones no altera el precio
    precio_borrado = (
        abs(float(fila[2]) - float(data.cantidad)) > 1e-9
        and borrar_precio_acordado(cur, evento_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        evento_id
    )

    return {
        "mensaje": "Arreglo actualizado",
        "precio_borrado": precio_borrado
    }

def eliminar_arreglo_evento(detalle_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT evento_id
        FROM evento_arreglos
        WHERE id = %s
    """, (detalle_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Detalle no encontrado"
        }

    evento_id = fila[0]

    cur.execute("""
        DELETE FROM evento_arreglos
        WHERE id = %s
    """, (detalle_id,))

    precio_borrado = borrar_precio_acordado(cur, evento_id)

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        evento_id
    )

    return {
        "mensaje": "Arreglo eliminado",
        "precio_borrado": precio_borrado
    }



def sincronizar_arreglo_en_eventos(arreglo_id):
    """Pasa la versión actual de un arreglo del catálogo a los eventos en negociación.

    Al agregar un arreglo a un evento se copian su costo y su receta. Si
    después se edita la receta en el catálogo, los eventos en Cotización o
    Pendiente Autorización toman el costo y la receta nuevos. Los confirmados
    o con contrato conservan la versión con la que se cerraron.

    Si el costo de la partida cambió, se borra el precio acordado del evento,
    igual que al cambiar sus arreglos (ver borrar_precio_acordado).
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT costo_total FROM arreglos WHERE id = %s", (arreglo_id,))
    fila = cur.fetchone()
    if not fila:
        cur.close()
        conn.close()
        return {"eventos_actualizados": 0, "precios_borrados": 0}

    costo = fila[0] or 0

    cur.execute("""
        SELECT ea.id, ea.evento_id, ea.costo_unitario
        FROM evento_arreglos ea
        INNER JOIN eventos e
            ON e.id = ea.evento_id
        WHERE ea.arreglo_id = %s
          AND e.activo = TRUE
          AND e.estatus = ANY(%s)
        ORDER BY ea.id
        FOR UPDATE OF ea
    """, (arreglo_id, ESTATUS_EN_NEGOCIACION))
    partidas = cur.fetchall()

    eventos, con_costo_nuevo = set(), set()
    for partida_id, evento_id, costo_anterior in partidas:
        cur.execute("""
            UPDATE evento_arreglos
            SET
                costo_unitario = %s,
                subtotal = cantidad * %s
            WHERE id = %s
        """, (costo, costo, partida_id))

        # La receta también cambia la lista de compras: se vuelve a copiar
        cur.execute("""
            DELETE FROM evento_arreglo_insumos
            WHERE evento_arreglo_id = %s
        """, (partida_id,))
        congelar_insumos_arreglo(cur, partida_id, arreglo_id)

        eventos.add(evento_id)
        if abs(float(costo_anterior or 0) - float(costo)) >= 0.005:
            con_costo_nuevo.add(evento_id)

    precios_borrados = sum(
        1 for evento_id in sorted(con_costo_nuevo)
        if borrar_precio_acordado(cur, evento_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    for evento_id in sorted(eventos):
        actualizar_totales_evento(evento_id)

    return {
        "eventos_actualizados": len(eventos),
        "precios_borrados": precios_borrados
    }
