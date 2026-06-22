from app.database.connection import get_connection


def obtener_arreglos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            codigo,
            nombre,
            categoria,
            descripcion,
            imagen_url,
            costo_total,
            activo,
            fecha_creacion
        FROM arreglos
        WHERE activo = TRUE
        ORDER BY id
    """)

    filas = cur.fetchall()
    columnas = [desc[0] for desc in cur.description]
    resultado = [dict(zip(columnas, fila)) for fila in filas]

    cur.close()
    conn.close()

    return resultado

def crear_arreglo(data):

    conn = get_connection()
    cur = conn.cursor()

    # Buscar último código
    cur.execute("""
        SELECT codigo
        FROM arreglos
        ORDER BY codigo DESC
        LIMIT 1
    """)

    ultimo = cur.fetchone()

    if ultimo:
        ultimo_numero = int(ultimo[0][3:])
        nuevo_numero  = ultimo_numero + 1
    else:
        nuevo_numero = 1

    nuevo_codigo = f"ARR{nuevo_numero:03d}"

    cur.execute("""
        INSERT INTO arreglos (
            codigo,
            nombre,
            categoria,
            descripcion,
            imagen_url,
            costo_total,
            activo
        )
        VALUES (
            %s, %s, %s, %s, %s, 0, TRUE
        )
        RETURNING id
    """, (
        nuevo_codigo,
        data.nombre,
        data.categoria,
        data.descripcion,
        data.imagen_url
    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"mensaje": "Arreglo creado", "id": nuevo_id, "codigo": nuevo_codigo}

def obtener_arreglo(arreglo_id):

    conn = get_connection()
    cur = conn.cursor()

    # Encabezado
    cur.execute("""
        SELECT
            id,
            codigo,
            nombre,
            categoria,
            descripcion,
            costo_total,
            activo,
            fecha_creacion
        FROM arreglos
        WHERE id = %s
    """, (arreglo_id,))

    arreglo = cur.fetchone()

    if not arreglo:

        cur.close()
        conn.close()

        return {
            "error": "Arreglo no encontrado"
        }

    columnas = [desc[0] for desc in cur.description]

    resultado = dict(zip(columnas, arreglo))

    # Detalle
    cur.execute("""
        SELECT

            ad.id,

            i.id AS insumo_id,
            i.codigo,
            i.nombre,

            ad.cantidad,
            ad.costo_real,

            (ad.cantidad * ad.costo_real) AS subtotal,

            ad.observaciones
        FROM arreglo_detalle ad

        INNER JOIN insumos i
            ON ad.insumo_id = i.id

        WHERE ad.arreglo_id = %s

        ORDER BY ad.id

    """, (arreglo_id,))

    filas = cur.fetchall()

    columnas = [desc[0] for desc in cur.description]

    detalle = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    resultado["insumos"] = detalle

    cur.close()
    conn.close()

    return resultado

def editar_arreglo(arreglo_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE arreglos
        SET
            nombre = %s,
            categoria = %s,
            descripcion = %s
        WHERE id = %s
    """, (

        data.nombre,
        data.categoria,
        data.descripcion,
        arreglo_id

    ))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Arreglo actualizado"
    }

def eliminar_arreglo(arreglo_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE arreglos
        SET activo = FALSE
        WHERE id = %s
    """, (arreglo_id,))

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Arreglo desactivado"
    }