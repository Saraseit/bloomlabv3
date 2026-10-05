from app.database.connection import get_connection
from app.services.compras_service import (
    calcular_costo_sobrante,
    copiar_insumos_congelados
)
from app.services.configuracion_service import obtener_parametros
from app.services.precios import (
    precio_para_margen,
    resultado_para_precio,
    repartir_por_arreglo
)

def obtener_eventos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,

            e.cliente_id,

            c.nombre AS cliente,

            e.nombre,

            e.tipo_evento,

            e.fecha_evento,

            e.lugar,

            e.descripcion,

            e.estatus,

            e.comision_porcentaje,

            e.costo_base,

            e.costo_final,

            e.precio_minimo,

            e.precio_sugerido,

            e.activo,

            e.fecha_creacion

        FROM eventos e

        INNER JOIN clientes c
            ON e.cliente_id = c.id

        WHERE e.activo = TRUE

        ORDER BY e.fecha_evento
    """)

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

def crear_evento(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO eventos (

            cliente_id,
            nombre,
            tipo_evento,
            fecha_evento,
            lugar,
            descripcion,
            estatus,
            comision_porcentaje,
            activo

        )
        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            TRUE

        )
        RETURNING id
    """, (

        data.cliente_id,
        data.nombre,
        data.tipo_evento,
        data.fecha_evento,
        data.lugar,
        data.descripcion,
        data.estatus,
        data.comision_porcentaje

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Evento creado",
        "id": nuevo_id
    }

def actualizar_evento(evento_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE eventos
        SET
            cliente_id = %s,
            nombre = %s,
            tipo_evento = %s,
            fecha_evento = %s,
            lugar = %s,
            descripcion = %s,
            estatus = %s
        WHERE id = %s
    """, (

        data.cliente_id,
        data.nombre,
        data.tipo_evento,
        data.fecha_evento,
        data.lugar,
        data.descripcion,
        data.estatus,
        evento_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Evento actualizado"
    }

def eliminar_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE eventos
        SET activo = FALSE
        WHERE id = %s
    """, (evento_id,))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Evento eliminado"
    }

def _calcular_totales(cur, evento_id):
    """Calcula los totales del evento con margen (ver services/precios.py).

    No escribe nada. El precio de referencia es el acordado si existe; si
    no, el sugerido. Comisión, ganancia y margen se miden a ese precio.
    """
    cur.execute("""
        SELECT costo_flete, costo_montaje, comision_porcentaje, precio_venta
        FROM eventos
        WHERE id = %s
    """, (evento_id,))
    fila = cur.fetchone()
    if not fila:
        return None

    costo_flete   = float(fila[0] or 0)
    costo_montaje = float(fila[1] or 0)
    comision_pct  = float(fila[2] or 0)
    precio_venta  = float(fila[3]) if fila[3] is not None else None

    cur.execute("""
        SELECT COALESCE(SUM(subtotal), 0)
        FROM evento_arreglos
        WHERE evento_id = %s
    """, (evento_id,))
    costo_arreglos = float(cur.fetchone()[0])

    # Paquetes incompletos: costo de material, va en el precio de arreglos
    costo_sobrante = calcular_costo_sobrante(cur, evento_id)

    parametros = obtener_parametros(cur)
    comision   = comision_pct / 100
    traslados  = costo_flete + costo_montaje

    precio_minimo = precio_para_margen(
        costo_arreglos, costo_sobrante, traslados, comision,
        parametros["margen_minimo"] / 100
    )
    precio_sugerido = precio_para_margen(
        costo_arreglos, costo_sobrante, traslados, comision,
        parametros["margen_objetivo"] / 100
    )

    if precio_venta is not None and precio_venta > 0:
        precio_referencia, tipo_precio = precio_venta, "acordado"
    elif precio_sugerido is not None:
        precio_referencia, tipo_precio = precio_sugerido, "sugerido"
    else:
        precio_referencia, tipo_precio = None, None

    resultado = (
        resultado_para_precio(
            costo_arreglos, costo_sobrante, traslados, comision, precio_referencia
        )
        if precio_referencia is not None else None
    )

    costo_directo    = costo_arreglos + costo_sobrante + traslados
    comision_importe = resultado["comision"] if resultado else 0.0

    advertencia = None
    if precio_sugerido is None:
        advertencia = (
            f"Con {comision_pct:g}% de comisión y {parametros['margen_objetivo']:g}% "
            "de margen objetivo no hay precio posible: entre los dos superan el 100% "
            "del precio de los arreglos."
        )

    return {
        "costo_arreglos":    costo_arreglos,
        "costo_flete":       costo_flete,
        "costo_montaje":     costo_montaje,
        "costo_sobrante":    costo_sobrante,
        "costo_directo":     costo_directo,
        "comision_pct":      comision_pct,
        "comision_importe":  comision_importe,
        # Todo lo que no es ganancia: costos + comisión al precio de referencia.
        # Reportes y utilidad real usan precio - costo_final.
        "costo_final":       costo_directo + comision_importe,
        "precio_minimo":     precio_minimo,
        "precio_sugerido":   precio_sugerido,
        "precio_venta":      precio_venta,
        "precio_referencia": precio_referencia,
        "tipo_precio":       tipo_precio,
        "precio_arreglos":   resultado["precio_arreglos"] if resultado else None,
        "ganancia":          resultado["ganancia"] if resultado else None,
        "margen":            resultado["margen"] if resultado else None,
        "parametros":        parametros,
        "advertencia":       advertencia,
    }


def actualizar_totales_evento(evento_id):
    """Recalcula y guarda los totales del evento."""

    conn = get_connection()
    cur = conn.cursor()

    t = _calcular_totales(cur, evento_id)
    if t is None:
        cur.close()
        conn.close()
        return None

    cur.execute("""
        UPDATE eventos
        SET
            costo_base       = %s,
            costo_sobrante   = %s,
            comision_importe = %s,
            costo_final      = %s,
            precio_minimo    = %s,
            precio_sugerido  = %s
        WHERE id = %s
    """, (
        t["costo_arreglos"],
        t["costo_sobrante"],
        t["comision_importe"],
        t["costo_final"],
        t["precio_minimo"],
        t["precio_sugerido"],
        evento_id,
    ))

    conn.commit()
    cur.close()
    conn.close()
    return t


def _redondear(valor, decimales=2):
    return round(valor, decimales) if valor is not None else None


def obtener_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,
            e.cliente_id,
            c.nombre AS cliente,
            e.nombre,
            e.tipo_evento,
            e.fecha_evento,
            e.lugar,
            e.descripcion,
            e.estatus,
            e.nota_autorizacion,
            e.activo,
            e.fecha_creacion

        FROM eventos e

        INNER JOIN clientes c
            ON e.cliente_id = c.id

        WHERE e.id = %s

    """, (evento_id,))

    evento = cur.fetchone()

    if not evento:
        cur.close()
        conn.close()
        return {"error": "Evento no encontrado"}

    columnas = [desc[0] for desc in cur.description]
    resultado = dict(zip(columnas, evento))

    # Totales al momento, con la fórmula de margen
    t = _calcular_totales(cur, evento_id)

    resultado.update({
        "costo_arreglos":      _redondear(t["costo_arreglos"]),
        # costo_base se conserva por compatibilidad: ahora es el costo de arreglos
        "costo_base":          _redondear(t["costo_arreglos"]),
        "costo_flete":         _redondear(t["costo_flete"]),
        "costo_montaje":       _redondear(t["costo_montaje"]),
        "costo_sobrante":      _redondear(t["costo_sobrante"]),
        "costo_directo":       _redondear(t["costo_directo"]),
        "comision_porcentaje": _redondear(t["comision_pct"]),
        "importe_comision":    _redondear(t["comision_importe"]),
        "costo_final":         _redondear(t["costo_final"]),
        "precio_minimo":       _redondear(t["precio_minimo"]),
        "precio_sugerido":     _redondear(t["precio_sugerido"]),
        "precio_venta":        _redondear(t["precio_venta"]),
        "precio_referencia":   _redondear(t["precio_referencia"]),
        "tipo_precio":         t["tipo_precio"],
        "ganancia":            _redondear(t["ganancia"]),
        "margen_efectivo":     _redondear(t["margen"] * 100) if t["margen"] is not None else None,
        "parametros":          t["parametros"],
        "advertencia":         t["advertencia"],
    })

    # Arreglos del evento, cada uno con su precio y su comisión
    cur.execute("""
        SELECT

            ea.id,
            ea.arreglo_id,
            a.codigo,
            a.nombre,
            a.imagen_url,
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
    columnas = [desc[0] for desc in cur.description]
    arreglos = [dict(zip(columnas, fila)) for fila in filas]

    partidas = repartir_por_arreglo(
        [float(a["subtotal"] or 0) for a in arreglos],
        t["precio_arreglos"] or 0.0,
        t["comision_pct"] / 100,
    )
    for arreglo, (precio, comision) in zip(arreglos, partidas):
        cantidad = float(arreglo["cantidad"] or 0)
        arreglo["precio_venta"] = round(precio, 2)
        arreglo["precio_unitario_venta"] = round(precio / cantidad, 2) if cantidad else 0.0
        arreglo["comision_porcentaje"] = _redondear(t["comision_pct"])
        arreglo["comision_importe"] = round(comision, 2)

    resultado["arreglos"] = arreglos

    cur.close()
    conn.close()

    return resultado


def _revisar_autorizacion(evento_id, usuario):
    """Si un vendedor deja el margen bajo el umbral, el evento espera autorización.

    Aplica cuando hay precio acordado; con precio sugerido no hay nada que
    autorizar todavía. Devuelve (requiere_autorizacion, totales).
    """
    conn = get_connection()
    cur = conn.cursor()

    t = _calcular_totales(cur, evento_id)
    umbral = t["parametros"]["margen_autorizacion"] / 100

    requiere = (
        t["tipo_precio"] == "acordado"
        and usuario["rol"] == "vendedor"
        and (t["margen"] if t["margen"] is not None else 0) < umbral
    )

    if requiere:
        cur.execute("""
            UPDATE eventos
            SET estatus = 'Pendiente Autorización'
            WHERE id = %s
        """, (evento_id,))
        conn.commit()

    cur.close()
    conn.close()
    return requiere, t


def fijar_precio_venta(evento_id, precio_venta, usuario):

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE eventos
        SET precio_venta = %s
        WHERE id = %s
        RETURNING id
    """, (precio_venta, evento_id))
    existe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not existe:
        return {"error": "Evento no encontrado"}

    # La comisión depende del precio: hay que recalcular antes de medir
    actualizar_totales_evento(evento_id)
    requiere, t = _revisar_autorizacion(evento_id, usuario)

    return {
        "mensaje": "Precio guardado",
        "requiere_autorizacion": requiere,
        "margen": round((t["margen"] or 0) * 100, 2),
        "ganancia": round(t["ganancia"] or 0, 2),
        "comision": round(t["comision_importe"], 2),
    }


def actualizar_comision(evento_id, porcentaje, usuario):

    parametros = obtener_parametros()

    if porcentaje < 0 or porcentaje >= 100:
        return {"error": "La comisión debe estar entre 0 y 99.99%."}

    if porcentaje + parametros["margen_objetivo"] >= 100:
        return {"error": (
            f"Con {porcentaje:g}% de comisión y {parametros['margen_objetivo']:g}% "
            "de margen objetivo no queda precio posible: entre los dos deben "
            "sumar menos de 100%."
        )}

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE eventos
        SET comision_porcentaje = %s
        WHERE id = %s
        RETURNING id
    """, (porcentaje, evento_id))
    existe = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not existe:
        return {"error": "Evento no encontrado"}

    actualizar_totales_evento(evento_id)

    # Más comisión = menos margen al precio ya acordado
    requiere, t = _revisar_autorizacion(evento_id, usuario)

    return {
        "mensaje": "Comisión actualizada",
        "requiere_autorizacion": requiere,
        "margen": round(t["margen"] * 100, 2) if t["margen"] is not None else None,
    }


def duplicar_evento(evento_id: int):

    """Crea una cotización nueva a partir de otro evento.

    Se copian cliente, datos descriptivos, gastos operativos y los
    arreglos con su costo_unitario tal como quedó guardado, sin
    recalcularlo desde el catálogo: el duplicado conserva los precios
    con los que se coticó el original.

    No se copian fecha, precio de venta, pagos, gastos reales ni la
    nota de autorización.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            cliente_id,
            nombre,
            tipo_evento,
            lugar,
            descripcion,
            costo_flete,
            costo_montaje,
            comision_porcentaje
        FROM eventos
        WHERE id = %s
          AND activo = TRUE
    """, (evento_id,))

    original = cur.fetchone()

    if not original:

        cur.close()
        conn.close()

        return {
            "error": "Evento no encontrado"
        }

    (cliente_id, nombre, tipo_evento, lugar,
     descripcion, costo_flete, costo_montaje, comision_porcentaje) = original

    # Los totales entran en cero y los recalcula
    # actualizar_totales_evento() al final.
    cur.execute("""
        INSERT INTO eventos (
            cliente_id,
            nombre,
            tipo_evento,
            lugar,
            descripcion,
            estatus,
            costo_flete,
            costo_montaje,
            comision_porcentaje,
            costo_base,
            costo_final,
            precio_minimo,
            precio_sugerido,
            activo
        )
        VALUES (
            %s, %s, %s, %s, %s, 'Cotizacion', %s, %s, %s, 0, 0, 0, 0, TRUE
        )
        RETURNING id
    """, (
        cliente_id,
        nombre + " (copia)",
        tipo_evento,
        lugar,
        descripcion,
        costo_flete,
        costo_montaje,
        comision_porcentaje
    ))

    nuevo_id = cur.fetchone()[0]

    # Renglón por renglón para copiar también la foto de insumos
    # (factor, costo de paquete) con la que se cotizó el original.
    cur.execute("""
        SELECT id, arreglo_id, cantidad, costo_unitario, subtotal, observaciones
        FROM evento_arreglos
        WHERE evento_id = %s
        ORDER BY id
    """, (evento_id,))

    for (ea_id, arreglo_id, cantidad, costo_unitario,
         subtotal, observaciones) in cur.fetchall():

        cur.execute("""
            INSERT INTO evento_arreglos (
                evento_id,
                arreglo_id,
                cantidad,
                costo_unitario,
                subtotal,
                observaciones
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (nuevo_id, arreglo_id, cantidad, costo_unitario,
              subtotal, observaciones))

        copiar_insumos_congelados(cur, ea_id, cur.fetchone()[0])

    conn.commit()

    cur.close()
    conn.close()

    actualizar_totales_evento(nuevo_id)

    return {
        "mensaje": "Evento duplicado",
        "id": nuevo_id
    }
