from app.database.connection import get_connection

from app.services.eventos_service import (
    actualizar_totales_evento
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

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        data.evento_id
    )
    return {
        "mensaje": "Arreglo agregado",
        "id": nuevo_id
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
            costo_unitario
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

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        evento_id
    )

    return {
        "mensaje": "Arreglo actualizado"
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

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(
        evento_id
    )

    return {
        "mensaje": "Arreglo eliminado"
    }

