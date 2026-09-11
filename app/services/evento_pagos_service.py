from app.database.connection import get_connection


def obtener_pagos_evento(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            id,

            evento_id,

            fecha,

            concepto,

            monto,

            metodo,

            notas,

            creado_en

        FROM evento_pagos

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
    for pago in resultado:
        pago["monto"] = float(pago["monto"])

    cur.close()
    conn.close()

    return resultado


def agregar_pago(evento_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evento_pagos (

            evento_id,
            fecha,
            concepto,
            monto,
            metodo,
            notas

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

        evento_id,
        data.fecha,
        data.concepto,
        data.monto,
        data.metodo,
        data.notas

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Pago registrado",
        "id": nuevo_id
    }


def editar_pago(pago_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE evento_pagos
        SET
            fecha = %s,
            concepto = %s,
            monto = %s,
            metodo = %s,
            notas = %s
        WHERE id = %s
        RETURNING id
    """, (

        data.fecha,
        data.concepto,
        data.monto,
        data.metodo,
        data.notas,
        pago_id

    ))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Pago no encontrado"
        }

    return {
        "mensaje": "Pago actualizado",
        "id": resultado[0]
    }


def eliminar_pago(pago_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM evento_pagos
        WHERE id = %s
        RETURNING id
    """, (pago_id,))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Pago no encontrado"
        }

    return {
        "mensaje": "Pago eliminado"
    }


def calcular_resumen_pagos(evento_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            COALESCE(SUM(monto), 0) AS total_pagado,

            COUNT(*) AS num_pagos

        FROM evento_pagos

        WHERE evento_id = %s
    """, (evento_id,))

    fila = cur.fetchone()

    total_pagado = float(fila[0])
    num_pagos = int(fila[1])

    cur.execute("""
        SELECT precio_venta
        FROM eventos
        WHERE id = %s
    """, (evento_id,))

    evento = cur.fetchone()

    cur.close()
    conn.close()

    # Sin precio acordado todavía no hay saldo que calcular
    if not evento or evento[0] is None:
        saldo_pendiente = None
    else:
        saldo_pendiente = round(
            float(evento[0]) - total_pagado,
            2
        )

    return {
        "total_pagado": round(total_pagado, 2),
        "num_pagos": num_pagos,
        "saldo_pendiente": saldo_pendiente
    }
