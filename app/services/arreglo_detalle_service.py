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
    
    actualizar_costo_total(
    data.arreglo_id
)
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

def actualizar_costo_total(arreglo_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COALESCE(
                SUM(cantidad * costo_real),
                0
            )
        FROM arreglo_detalle
        WHERE arreglo_id = %s
    """, (arreglo_id,))

    total = cur.fetchone()[0]

    cur.execute("""
        UPDATE arreglos
        SET costo_total = %s
        WHERE id = %s
    """, (
        total,
        arreglo_id
    ))

    conn.commit()

    cur.close()
    conn.close()

 
def editar_detalle(detalle_id, data):

    conn = get_connection()
    cur = conn.cursor()

    # Obtener arreglo_id antes de modificar
    cur.execute("""
        SELECT arreglo_id
        FROM arreglo_detalle
        WHERE id = %s
    """, (detalle_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Detalle no encontrado"
        }

    arreglo_id = fila[0]

    cur.execute("""
        UPDATE arreglo_detalle
        SET
            cantidad = %s,
            costo_real = %s,
            observaciones = %s
        WHERE id = %s
    """, (

        data.cantidad,
        data.costo_real,
        data.observaciones,
        detalle_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    actualizar_costo_total(arreglo_id)

    return {
        "mensaje": "Detalle actualizado"
    }  

def eliminar_detalle(detalle_id):

    conn = get_connection()
    cur = conn.cursor()

    # Obtener arreglo relacionado
    cur.execute("""
        SELECT arreglo_id
        FROM arreglo_detalle
        WHERE id = %s
    """, (detalle_id,))

    fila = cur.fetchone()

    if not fila:

        cur.close()
        conn.close()

        return {
            "error": "Detalle no encontrado"
        }

    arreglo_id = fila[0]

    # Eliminar registro
    cur.execute("""
        DELETE FROM arreglo_detalle
        WHERE id = %s
    """, (detalle_id,))

    conn.commit()

    cur.close()
    conn.close()

    actualizar_costo_total(arreglo_id)

    return {
        "mensaje": "Detalle eliminado"
    } 