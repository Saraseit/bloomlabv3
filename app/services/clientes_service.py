from app.database.connection import get_connection


def obtener_clientes():

    conn = get_connection()
    cur = conn.cursor()

    # deuda_total sale en la misma consulta para no hacer N+1.
    #
    # Los pagos se suman por evento en una subconsulta antes de unirlos:
    # si se uniera evento_pagos directo, un evento con N pagos aparecería
    # en N renglones y SUM(e.precio_venta) contaría el precio N veces.
    cur.execute("""
        SELECT
            c.id,
            c.nombre,
            c.telefono,
            c.email,
            c.empresa,
            c.notas,
            c.comision_porcentaje,
            c.activo,
            c.fecha_creacion,

            COALESCE(SUM(e.precio_venta) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
            - COALESCE(SUM(pg.pagado) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
                AS deuda_total

        FROM clientes c

        LEFT JOIN eventos e
            ON e.cliente_id = c.id

        LEFT JOIN (
            SELECT
                evento_id,
                SUM(monto) AS pagado
            FROM evento_pagos
            GROUP BY evento_id
        ) pg
            ON pg.evento_id = e.id

        WHERE c.activo = TRUE

        GROUP BY
            c.id,
            c.nombre,
            c.telefono,
            c.email,
            c.empresa,
            c.notas,
            c.comision_porcentaje,
            c.activo,
            c.fecha_creacion

        ORDER BY c.nombre
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

    for cliente in resultado:
        cliente["deuda_total"] = round(
            float(cliente["deuda_total"] or 0), 2
        )

    cur.close()
    conn.close()

    return resultado


def obtener_cliente_detalle(cliente_id):

    conn = get_connection()
    cur = conn.cursor()

    # Los pagos se agregan por evento antes de unirlos al cliente.
    # Uniendo evento_pagos directamente, un evento confirmado con N pagos
    # se repetiría en N renglones y SUM(e.precio_venta) inflaría
    # total_facturado y deuda_total N veces.
    cur.execute("""
        SELECT

            c.id,
            c.nombre,
            c.telefono,
            c.email,
            c.empresa,
            c.comision_porcentaje,

            COUNT(DISTINCT e.id) FILTER (WHERE e.activo)
                AS total_eventos,

            COUNT(DISTINCT e.id) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado')
                AS eventos_confirmados,

            COALESCE(SUM(e.precio_venta) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
                AS total_facturado,

            COALESCE(SUM(pg.pagado) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
                AS total_cobrado,

            COALESCE(SUM(e.precio_venta) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
            - COALESCE(SUM(pg.pagado) FILTER (
                WHERE e.activo AND e.estatus = 'Confirmado'), 0)
                AS deuda_total

        FROM clientes c

        LEFT JOIN eventos e
            ON e.cliente_id = c.id

        LEFT JOIN (
            SELECT
                evento_id,
                SUM(monto) AS pagado
            FROM evento_pagos
            GROUP BY evento_id
        ) pg
            ON pg.evento_id = e.id

        WHERE c.id = %s

        GROUP BY
            c.id,
            c.nombre,
            c.telefono,
            c.email,
            c.empresa,
            c.comision_porcentaje
    """, (cliente_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Cliente no encontrado"
        }

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = dict(zip(columnas, fila))

    resultado["total_facturado"] = round(
        float(resultado["total_facturado"] or 0), 2
    )
    resultado["total_cobrado"] = round(
        float(resultado["total_cobrado"] or 0), 2
    )
    resultado["deuda_total"] = round(
        float(resultado["deuda_total"] or 0), 2
    )
    resultado["comision_porcentaje"] = float(
        resultado["comision_porcentaje"] or 0
    )

    # Historial de eventos del cliente
    cur.execute("""
        SELECT

            e.id,
            e.nombre,
            e.tipo_evento,
            e.fecha_evento,
            e.estatus,
            e.precio_venta,

            COALESCE(SUM(p.monto), 0) AS pagado

        FROM eventos e

        LEFT JOIN evento_pagos p
            ON p.evento_id = e.id

        WHERE e.cliente_id = %s
          AND e.activo

        GROUP BY e.id

        ORDER BY e.fecha_evento DESC
    """, (cliente_id,))

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    eventos = [
        dict(zip(columnas, f))
        for f in filas
    ]

    for evento in eventos:
        evento["precio_venta"] = (
            round(float(evento["precio_venta"]), 2)
            if evento["precio_venta"] is not None
            else None
        )
        evento["pagado"] = round(float(evento["pagado"] or 0), 2)

    resultado["eventos"] = eventos

    cur.close()
    conn.close()

    return resultado


def crear_cliente(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO clientes (

            nombre,
            telefono,
            email,
            empresa,
            notas,
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
            TRUE
        )
        RETURNING id
    """, (

        data.nombre,
        data.telefono,
        data.email,
        data.empresa,
        data.notas,
        data.comision_porcentaje

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente creado",
        "id": nuevo_id
    }

def actualizar_cliente(cliente_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE clientes
        SET
            nombre = %s,
            telefono = %s,
            email = %s,
            empresa = %s,
            notas = %s,
            comision_porcentaje = %s
        WHERE id = %s
    """, (

        data.nombre,
        data.telefono,
        data.email,
        data.empresa,
        data.notas,
        data.comision_porcentaje,
        cliente_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente actualizado"
    }

def eliminar_cliente(cliente_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE clientes
        SET activo = FALSE
        WHERE id = %s
    """, (cliente_id,))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Cliente eliminado"
    }

