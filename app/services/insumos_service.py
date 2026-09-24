from decimal import Decimal

from app.database.connection import get_connection


# ──────────────────────────────────────────────
# Merma: la base guarda el decimal (0.10),
# el usuario y el frontend usan el entero (10).
# ──────────────────────────────────────────────

def merma_a_decimal(valor):
    """Entero capturado por el usuario (10) -> decimal para la base (0.10)."""
    return (Decimal(str(valor or 0)) / 100)


def merma_a_entero(valor):
    """Decimal de la base (0.10) -> entero para el frontend (10)."""
    return float(Decimal(str(valor or 0)) * 100)


def obtener_insumos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            i.id,
            i.codigo,
            i.nombre,
            i.categoria_id,
            c.nombre AS categoria,
            i.unidad,
            i.costo_referencia,
            i.porcentaje_merma,
            i.unidad_uso,
            i.piezas_por_paquete,
            i.cobrar_paquete_completo,
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

    # La base guarda el decimal (0.10); el frontend siempre recibe
    # el entero (10). Se multiplica sobre el Decimal para evitar
    # errores de coma flotante (0.1 * 100 = 10.000000000000002).
    for insumo in resultado:
        insumo["porcentaje_merma"] = merma_a_entero(
            insumo["porcentaje_merma"]
        )
        insumo["piezas_por_paquete"] = float(insumo["piezas_por_paquete"] or 1)
        # Sin unidad de uso capturada, se usa la de compra
        insumo["unidad_uso"] = (
            (insumo["unidad_uso"] or "").strip() or insumo["unidad"]
        )

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
            unidad_uso,
            piezas_por_paquete,
            cobrar_paquete_completo,
            activo
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
        merma_a_decimal(data.porcentaje_merma),
        _unidad_uso(data),
        data.piezas_por_paquete,
        data.cobrar_paquete_completo
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

def _unidad_uso(data):
    """Unidad de uso capturada, o None si viene vacía (= unidad de compra)."""
    return (data.unidad_uso or "").strip() or None


def _normalizar(texto):
    return (texto or "").strip().lower()


def actualizar_insumo(insumo_id, data):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT unidad, unidad_uso, piezas_por_paquete
        FROM insumos
        WHERE id = %s
        FOR UPDATE
    """, (insumo_id,))

    anterior = cur.fetchone()

    if not anterior:
        cur.close()
        conn.close()
        return {
            "error": "Insumo no encontrado"
        }

    unidad_ant, unidad_uso_ant, factor_ant = anterior
    factor_ant = float(factor_ant or 1)
    uso_ant = _normalizar(unidad_uso_ant) or _normalizar(unidad_ant)
    uso_nuevo = _normalizar(data.unidad_uso) or _normalizar(data.unidad)

    cur.execute("""
        UPDATE insumos
        SET
            nombre = %s,
            categoria_id = %s,
            unidad = %s,
            costo_referencia = %s,
            porcentaje_merma = %s,
            unidad_uso = %s,
            piezas_por_paquete = %s,
            cobrar_paquete_completo = %s
        WHERE id = %s
    """, (
        data.nombre,
        data.categoria_id,
        data.unidad,
        data.costo_referencia,
        merma_a_decimal(data.porcentaje_merma),
        _unidad_uso(data),
        data.piezas_por_paquete,
        data.cobrar_paquete_completo,
        insumo_id
    ))

    # Si la unidad de compra sigue igual pero cambió la de uso y el factor
    # (ej. "PAQ 24" con factor 1 pasa a "tallo" con factor 24), los arreglos
    # del catálogo tenían la cantidad en la unidad vieja (0.5 paquete).
    # Se convierten a la nueva (12 tallos) ajustando el costo por unidad en
    # sentido inverso, así el subtotal de cada renglón no cambia.
    # Las cotizaciones ya hechas no se tocan: usan su propia foto.
    convertidos = 0
    if (
        _normalizar(unidad_ant) == _normalizar(data.unidad)
        and uso_ant != uso_nuevo
        and factor_ant != float(data.piezas_por_paquete)
    ):
        cur.execute("""
            UPDATE arreglo_detalle
            SET
                cantidad   = cantidad   * %s::numeric / %s::numeric,
                costo_real = costo_real * %s::numeric / %s::numeric
            WHERE insumo_id = %s
        """, (
            data.piezas_por_paquete, factor_ant,
            factor_ant, data.piezas_por_paquete,
            insumo_id
        ))
        convertidos = cur.rowcount

    conn.commit()

    cur.close()
    conn.close()

    return {
        "mensaje": "Insumo actualizado",
        "id": insumo_id,
        "detalles_convertidos": convertidos
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

def obtener_categorias_insumo():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            nombre,
            codigo
        FROM categorias_insumo
        ORDER BY nombre
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