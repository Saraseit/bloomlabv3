from app.database.connection import get_connection


# ──────────────────────────────────────────────
# Reportes financieros: todo es de solo lectura.
# Ninguna función de este módulo escribe en la base.
# ──────────────────────────────────────────────


def resumen_general():

    """KPIs globales del negocio"""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        WITH confirmados AS (
            SELECT
                e.id,
                e.precio_venta,
                e.costo_final,
                e.fecha_evento,
                e.cliente_id,
                COALESCE(SUM(gr.monto), 0) AS gastos_reales
            FROM eventos e
            LEFT JOIN evento_gastos_reales gr
                ON gr.evento_id = e.id
            WHERE e.activo
              AND e.estatus = 'Confirmado'
              AND e.precio_venta IS NOT NULL
            GROUP BY e.id, e.precio_venta, e.costo_final,
                     e.fecha_evento, e.cliente_id
        ),
        pagos AS (
            SELECT
                evento_id,
                COALESCE(SUM(monto), 0) AS total_pagado
            FROM evento_pagos
            GROUP BY evento_id
        )
        SELECT
            COUNT(*)                                   AS eventos_confirmados,
            COALESCE(SUM(c.precio_venta), 0)           AS ingresos_totales,
            COALESCE(SUM(c.costo_final), 0)            AS costos_totales,
            COALESCE(SUM(c.precio_venta - c.costo_final
                         - c.gastos_reales), 0)        AS utilidad_real,
            COALESCE(AVG(
                CASE WHEN c.precio_venta > 0
                THEN (c.precio_venta - c.costo_final) / c.precio_venta * 100
                END), 0)                               AS margen_promedio,
            COALESCE(SUM(p.total_pagado), 0)           AS total_cobrado,
            COALESCE(SUM(c.precio_venta)
                - SUM(COALESCE(p.total_pagado, 0)), 0) AS cartera_pendiente
        FROM confirmados c
        LEFT JOIN pagos p
            ON p.evento_id = c.id
    """)

    fila = cur.fetchone()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = dict(zip(columnas, fila))

    resultado["eventos_confirmados"] = int(
        resultado["eventos_confirmados"] or 0
    )

    for clave in ("ingresos_totales", "costos_totales", "utilidad_real",
                  "margen_promedio", "total_cobrado", "cartera_pendiente"):
        resultado[clave] = round(float(resultado[clave] or 0), 2)

    cur.close()
    conn.close()

    return resultado


def eventos_por_mes():

    """Ingresos y cantidad de eventos por mes (últimos 12 meses)"""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            TO_CHAR(fecha_evento, 'YYYY-MM')  AS mes,
            COUNT(*)                          AS cantidad,
            COALESCE(SUM(precio_venta), 0)    AS ingresos
        FROM eventos
        WHERE activo
          AND estatus = 'Confirmado'
          AND precio_venta IS NOT NULL
          AND fecha_evento >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY mes
        ORDER BY mes
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

    for renglon in resultado:
        renglon["cantidad"] = int(renglon["cantidad"] or 0)
        renglon["ingresos"] = round(float(renglon["ingresos"] or 0), 2)

    cur.close()
    conn.close()

    return resultado


def top_clientes(limite: int = 10):

    """Clientes con mayor facturación"""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            c.nombre,
            COUNT(DISTINCT e.id)             AS eventos,
            COALESCE(SUM(e.precio_venta), 0) AS facturado,
            COALESCE(SUM(e.precio_venta)
                - SUM(COALESCE(p.pagado, 0)), 0) AS deuda
        FROM clientes c
        JOIN eventos e
            ON e.cliente_id = c.id
           AND e.activo
           AND e.estatus = 'Confirmado'
           AND e.precio_venta IS NOT NULL
        LEFT JOIN (
            SELECT
                evento_id,
                SUM(monto) AS pagado
            FROM evento_pagos
            GROUP BY evento_id
        ) p
            ON p.evento_id = e.id
        WHERE c.activo
        GROUP BY c.id, c.nombre
        ORDER BY facturado DESC
        LIMIT %s
    """, (limite,))

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    for renglon in resultado:
        renglon["eventos"] = int(renglon["eventos"] or 0)
        renglon["facturado"] = round(float(renglon["facturado"] or 0), 2)
        renglon["deuda"] = round(float(renglon["deuda"] or 0), 2)

    cur.close()
    conn.close()

    return resultado


def top_arreglos(limite: int = 10):

    """Arreglos más utilizados en eventos confirmados"""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            a.nombre,
            a.categoria,
            COUNT(*)                           AS veces_usado,
            COALESCE(SUM(ea.cantidad), 0)      AS unidades_totales,
            COALESCE(AVG(ea.costo_unitario), 0) AS costo_promedio
        FROM evento_arreglos ea
        JOIN arreglos a
            ON a.id = ea.arreglo_id
        JOIN eventos e
            ON e.id = ea.evento_id
           AND e.activo
           AND e.estatus = 'Confirmado'
        GROUP BY a.id, a.nombre, a.categoria
        ORDER BY veces_usado DESC
        LIMIT %s
    """, (limite,))

    filas = cur.fetchall()

    columnas = [
        desc[0]
        for desc in cur.description
    ]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    for renglon in resultado:
        renglon["veces_usado"] = int(renglon["veces_usado"] or 0)
        renglon["unidades_totales"] = round(
            float(renglon["unidades_totales"] or 0), 2
        )
        renglon["costo_promedio"] = round(
            float(renglon["costo_promedio"] or 0), 2
        )

    cur.close()
    conn.close()

    return resultado


def rentabilidad_por_evento():

    """Lista de eventos confirmados con sus métricas de rentabilidad"""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.id,
            e.nombre,
            e.tipo_evento,
            e.fecha_evento,
            c.nombre                       AS cliente,
            e.precio_venta,
            e.costo_final,
            COALESCE(SUM(gr.monto), 0)     AS gastos_reales,
            e.precio_venta - e.costo_final
                - COALESCE(SUM(gr.monto), 0) AS utilidad,
            CASE WHEN e.precio_venta > 0
                THEN ROUND((e.precio_venta - e.costo_final)
                    / e.precio_venta * 100, 2)
                ELSE 0 END                 AS margen_pct
        FROM eventos e
        JOIN clientes c
            ON c.id = e.cliente_id
        LEFT JOIN evento_gastos_reales gr
            ON gr.evento_id = e.id
        WHERE e.activo
          AND e.estatus = 'Confirmado'
          AND e.precio_venta IS NOT NULL
        GROUP BY e.id, e.nombre, e.tipo_evento, e.fecha_evento,
                 c.nombre, e.precio_venta, e.costo_final
        ORDER BY e.fecha_evento DESC
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

    # Los NUMERIC de PostgreSQL llegan como Decimal y el frontend los
    # opera como números
    for renglon in resultado:
        for clave in ("precio_venta", "costo_final", "gastos_reales",
                      "utilidad", "margen_pct"):
            renglon[clave] = round(float(renglon[clave] or 0), 2)

    cur.close()
    conn.close()

    return resultado
