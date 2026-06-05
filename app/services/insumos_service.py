from app.database.connection import get_connection


def obtener_insumos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            i.id,
            i.codigo,
            i.nombre,
            c.nombre AS categoria,
            i.unidad,
            i.costo_referencia,
            i.porcentaje_merma,
            i.activo,
            i.fecha_creacion
        FROM insumos i
        INNER JOIN categorias_insumo c
            ON i.categoria_id = c.id
        WHERE i.activo = TRUE
        ORDER BY i.id
    """)

    filas = cur.fetchall()

    columnas = [desc[0] for desc in cur.description]

    resultado = [
        dict(zip(columnas, fila))
        for fila in filas
    ]

    cur.close()
    conn.close()

    return resultado


def crear_insumo(data):

    conn = get_connection()
    cur = conn.cursor()

    # Obtener prefijo de categoría
    cur.execute("""
        SELECT codigo
        FROM categorias_insumo
        WHERE id = %s
    """, (data.categoria_id,))

    categoria = cur.fetchone()

    if not categoria:
        cur.close()
        conn.close()

        return {
            "error": "Categoría no encontrada"
        }

    prefijo = categoria[0]

    # Buscar último código de la categoría
    cur.execute("""
        SELECT codigo
        FROM insumos
        WHERE codigo LIKE %s
        ORDER BY codigo DESC
        LIMIT 1
    """, (f"{prefijo}%",))

    ultimo = cur.fetchone()

    if ultimo:
        ultimo_numero = int(ultimo[0][3:])
        nuevo_numero = ultimo_numero + 1
    else:
        nuevo_numero = 1

    nuevo_codigo = f"{prefijo}{nuevo_numero:03d}"

    cur.execute("""
        INSERT INTO insumos (
            codigo,
            nombre,
            categoria_id,
            unidad,
            costo_referencia,
            porcentaje_merma,
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
        nuevo_codigo,
        data.nombre,
        data.categoria_id,
        data.unidad,
        data.costo_referencia,
        data.porcentaje_merma
    ))

    nuevo_id = cur.fetchone()[0]

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Insumo creado",
        "id": nuevo_id,
        "codigo": nuevo_codigo
    }

def actualizar_insumo(insumo_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE insumos
        SET
            nombre = %s,
            categoria_id = %s,
            unidad = %s,
            costo_referencia = %s,
            porcentaje_merma = %s
        WHERE id = %s
        RETURNING id
    """, (
        data.nombre,
        data.categoria_id,
        data.unidad,
        data.costo_referencia,
        data.porcentaje_merma,
        insumo_id
    ))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Insumo no encontrado"
        }

    return {
        "mensaje": "Insumo actualizado",
        "id": resultado[0]
    }

def eliminar_insumo(insumo_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE insumos
        SET activo = FALSE
        WHERE id = %s
        RETURNING id
    """, (insumo_id,))

    resultado = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    if not resultado:
        return {
            "error": "Insumo no encontrado"
        }

    return {
        "mensaje": "Insumo desactivado",
        "id": resultado[0]
    }