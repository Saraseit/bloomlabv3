from app.database.connection import get_connection


def agregar_insumo_arreglo(data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO arreglo_detalle (

            arreglo_id,
            insumo_id,
            cantidad,
            costo_real,
            observaciones

        )
        VALUES (

            %s,
            %s,
            %s,
            %s,
            %s

        )
        RETURNING id
    """, (

        data.arreglo_id,
        data.insumo_id,
        data.cantidad,
        data.costo_real,
        data.observaciones

    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Detalle agregado",
        "id": nuevo_id
    }

def obtener_detalle_arreglo(arreglo_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT

            ad.id,
            ad.arreglo_id,

            i.id AS insumo_id,
            i.codigo,
            i.nombre,
            ci.nombre AS categoria,

            ad.cantidad,
            ad.costo_real,

            (ad.cantidad * ad.costo_real) AS subtotal,

            ad.observaciones

        FROM arreglo_detalle ad

        INNER JOIN insumos i
            ON ad.insumo_id = i.id

        INNER JOIN categorias_insumo ci
            ON i.categoria_id = ci.id

        WHERE ad.arreglo_id = %s

        ORDER BY ad.id

    """, (arreglo_id,))

    filas = cur.fetchall()

    columnas = [desc[0] for desc in cur.description]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    cur.close()
    conn.close()

    return resultado