from app.database.connection import get_connection
def obtener_eventos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,

            e.cliente_id,

            c.nombre AS cliente,

            e.nombre,

            e.fecha_evento,

            e.lugar,

            e.descripcion,

            e.estatus,

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
            fecha_evento,
            lugar,
            descripcion,
            estatus,
            activo

        )
        VALUES (

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
        data.fecha_evento,
        data.lugar,
        data.descripcion,
        data.estatus

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
            fecha_evento = %s,
            lugar = %s,
            descripcion = %s,
            estatus = %s
        WHERE id = %s
    """, (

        data.cliente_id,
        data.nombre,
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

def actualizar_totales_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    MARGEN_MINIMO   = 0.30
    MARGEN_OBJETIVO = 0.40

    # Costo de arreglos
    cur.execute("""
        SELECT COALESCE(SUM(subtotal), 0)
        FROM evento_arreglos
        WHERE evento_id = %s
    """, (evento_id,))
    costo_arreglos = float(cur.fetchone()[0])

    # Gastos operativos del evento
    cur.execute("""
        SELECT costo_flete, costo_montaje
        FROM eventos
        WHERE id = %s
    """, (evento_id,))
    fila_gastos = cur.fetchone()
    costo_flete   = float(fila_gastos[0] or 0)
    costo_montaje = float(fila_gastos[1] or 0)

    # Comisión del cliente — SOLO sobre arreglos
    cur.execute("""
        SELECT c.comision_porcentaje
        FROM eventos e
        INNER JOIN clientes c ON e.cliente_id = c.id
        WHERE e.id = %s
    """, (evento_id,))
    fila = cur.fetchone()
    comision_porcentaje = float(fila[0]) if fila and fila[0] is not None else 0

    comision = costo_arreglos * (comision_porcentaje / 100)   # ← solo arreglos

    # costo_base ahora representa: arreglos + comisión (sin gastos)
    costo_base = costo_arreglos + comision

    # costo_final agrega los gastos operativos DESPUÉS de comisión
    costo_final = costo_base + costo_flete + costo_montaje

    precio_minimo   = costo_final / (1 - MARGEN_MINIMO)
    precio_sugerido = costo_final / (1 - MARGEN_OBJETIVO)

    cur.execute("""
        UPDATE eventos
        SET
            costo_base      = %s,
            costo_final     = %s,
            precio_minimo   = %s,
            precio_sugerido = %s
        WHERE id = %s
    """, (costo_base, costo_final, precio_minimo, precio_sugerido, evento_id))

    conn.commit()
    cur.close()
    conn.close()

def obtener_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            e.id,
            e.cliente_id,
            c.nombre AS cliente,
            c.comision_porcentaje,
            e.nombre,
            e.fecha_evento,
            e.lugar,
            e.descripcion,
            e.estatus,
            e.costo_base,
            e.costo_flete,
            e.costo_montaje,
            e.costo_final,
            e.precio_minimo,
            e.precio_sugerido,
            e.precio_venta,
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

    # Redondeos base
    costo_base    = round(resultado["costo_base"]    or 0, 2)
    costo_flete   = round(resultado["costo_flete"]   or 0, 2)
    costo_montaje = round(resultado["costo_montaje"] or 0, 2)
    costo_final   = round(resultado["costo_final"]   or 0, 2)
    comision_pct  = float(resultado["comision_porcentaje"] or 0)

    resultado["costo_base"]    = costo_base
    resultado["costo_flete"]   = costo_flete
    resultado["costo_montaje"] = costo_montaje
    resultado["costo_final"]   = costo_final

    resultado["precio_minimo"]   = round(resultado["precio_minimo"]   or 0, 2)
    resultado["precio_sugerido"] = round(resultado["precio_sugerido"] or 0, 2)
    resultado["precio_venta"]    = round(resultado["precio_venta"]    or 0, 2)

    # costo_base = costo_arreglos + comision (flete/montaje van aparte)
    # costo_arreglos = costo_base / (1 + comision_pct/100)
    if comision_pct > 0:
        costo_arreglos = float(costo_base) / (1 + comision_pct / 100)
    else:
        costo_arreglos = costo_base

    resultado["costo_arreglos"]   = round(costo_arreglos, 2)
    resultado["importe_comision"] = round(costo_base - costo_arreglos, 2)

    # Arreglos del evento
    cur.execute("""
        SELECT

            ea.id,
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
    columnas = [desc[0] for desc in cur.description]
    arreglos = [dict(zip(columnas, fila)) for fila in filas]

    resultado["arreglos"] = arreglos

    cur.close()
    conn.close()

    return resultado