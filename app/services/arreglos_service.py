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

# Número fijo para pg_advisory_xact_lock: dos altas a la vez no reciben el mismo código
_LOCK_CODIGO_ARREGLO = 874_201_554


def _siguiente_codigo(cur):
    """Siguiente código ARR libre. Corre en la transacción del llamador.

    Se toma el mayor número y no el mayor texto: como texto, "ARR999" va
    después de "ARR1000" y el código se repetiría al pasar de 999.
    """
    cur.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_CODIGO_ARREGLO,))
    cur.execute("""
        SELECT COALESCE(MAX(CAST(SUBSTRING(codigo FROM 4) AS INTEGER)), 0)
        FROM arreglos
        WHERE codigo ~ '^ARR[0-9]+$'
    """)
    return f"ARR{cur.fetchone()[0] + 1:03d}"


def crear_arreglo(data):

    conn = get_connection()
    cur = conn.cursor()

    nuevo_codigo = _siguiente_codigo(cur)

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
            imagen_url,
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
        return {"error": "Arreglo no encontrado"}

    columnas = [desc[0] for desc in cur.description]
    resultado = dict(zip(columnas, arreglo))

    # Detalle
    cur.execute("""
        SELECT
            ad.id,
            i.id AS insumo_id,
            i.codigo,
            i.nombre,
            i.unidad AS unidad_compra,
            COALESCE(NULLIF(TRIM(i.unidad_uso), ''), i.unidad) AS unidad_uso,
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
    detalle = [dict(zip(columnas, fila)) for fila in filas]

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
            nombre      = %s,
            categoria   = %s,
            descripcion = %s,
            imagen_url  = %s
        WHERE id = %s
    """, (
        data.nombre,
        data.categoria,
        data.descripcion,
        data.imagen_url,
        arreglo_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return {"mensaje": "Arreglo actualizado"}

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


def duplicar_arreglo(arreglo_id, nombre):
    """Crea un arreglo nuevo con la receta, la foto y la descripción de otro.

    El nuevo recibe su propio código y queda independiente: editarlo no
    cambia el original ni los eventos que usan el original.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT codigo, categoria, descripcion, imagen_url
        FROM arreglos
        WHERE id = %s AND activo = TRUE
    """, (arreglo_id,))
    original = cur.fetchone()

    if not original:
        cur.close()
        conn.close()
        return {"error": "Arreglo no encontrado"}

    codigo_original, categoria, descripcion, imagen_url = original
    nuevo_codigo = _siguiente_codigo(cur)

    cur.execute("""
        INSERT INTO arreglos (
            codigo, nombre, categoria, descripcion, imagen_url, costo_total, activo
        )
        VALUES (%s, %s, %s, %s, %s, 0, TRUE)
        RETURNING id
    """, (nuevo_codigo, nombre, categoria, descripcion, imagen_url))
    nuevo_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO arreglo_detalle (arreglo_id, insumo_id, cantidad, costo_real, observaciones)
        SELECT %s, insumo_id, cantidad, costo_real, observaciones
        FROM arreglo_detalle
        WHERE arreglo_id = %s
        ORDER BY id
    """, (nuevo_id, arreglo_id))
    insumos = cur.rowcount

    cur.execute("""
        UPDATE arreglos
        SET costo_total = (
            SELECT COALESCE(SUM(cantidad * costo_real), 0)
            FROM arreglo_detalle
            WHERE arreglo_id = %s
        )
        WHERE id = %s
        RETURNING costo_total
    """, (nuevo_id, nuevo_id))
    costo_total = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {
        "mensaje": "Arreglo duplicado",
        "id": nuevo_id,
        "codigo": nuevo_codigo,
        "codigo_original": codigo_original,
        "insumos": insumos,
        "costo_total": float(costo_total or 0),
    }
