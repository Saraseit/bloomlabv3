from app.database.connection import get_connection


def _paquetes(data):
    """Los paquetes solo tienen sentido si el gasto está ligado a un insumo."""
    return data.paquetes_comprados if data.insumo_id else None


def obtener_gastos_reales(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            id,

            evento_id,

            fecha,

            categoria,

            concepto,

            monto,

            es_reembolsable,

            notas,

            insumo_id,

            paquetes_comprados,

            creado_en

        FROM evento_gastos_reales

        WHERE evento_id = %s

        ORDER BY fecha, id
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

    # monto viaja como Decimal desde la base; el frontend lo usa como número
    for gasto in resultado:
        gasto["monto"] = float(gasto["monto"])
        if gasto["paquetes_comprados"] is not None:
            gasto["paquetes_comprados"] = float(gasto["paquetes_comprados"])

    cur.close()
    conn.close()

    return resultado


def agregar_gasto_real(evento_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evento_gastos_reales (

            evento_id,
            fecha,
            categoria,
            concepto,
            monto,
            es_reembolsable,
            notas,
            insumo_id,
            paquetes_comprados

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
            %s

        )
        RETURNING id
    """, (

        evento_id,
        data.fecha,
        data.categoria,
        data.concepto,
        data.monto,
        data.es_reembolsable,
        data.notas,
        data.insumo_id,
        _paquetes(data)

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Gasto registrado",
        "id": nuevo_id
    }


def editar_gasto_real(gasto_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE evento_gastos_reales
        SET
            fecha = %s,
            categoria = %s,
            concepto = %s,
            monto = %s,
            es_reembolsable = %s,
            notas = %s,
            insumo_id = %s,
            paquetes_comprados = %s
        WHERE id = %s
        RETURNING id
    """, (

        data.fecha,
        data.categoria,
        data.concepto,
        data.monto,
        data.es_reembolsable,
        data.notas,
        data.insumo_id,
        _paquetes(data),
        gasto_id

    ))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Gasto no encontrado"
        }

    return {
        "mensaje": "Gasto actualizado",
        "id": resultado[0]
    }


def eliminar_gasto_real(gasto_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM evento_gastos_reales
        WHERE id = %s
        RETURNING id
    """, (gasto_id,))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Gasto no encontrado"
        }

    return {
        "mensaje": "Gasto eliminado"
    }


def calcular_resumen_gastos_reales(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            COALESCE(SUM(monto), 0) AS total_gastos,

            COALESCE(
                SUM(CASE WHEN es_reembolsable THEN monto END),
                0
            ) AS gastos_reembolsables

        FROM evento_gastos_reales

        WHERE evento_id = %s
    """, (evento_id,))

    fila = cur.fetchone()

    cur.close()
    conn.close()

    return {
        "total_gastos": round(float(fila[0]), 2),
        "gastos_reembolsables": round(float(fila[1]), 2)
    }
