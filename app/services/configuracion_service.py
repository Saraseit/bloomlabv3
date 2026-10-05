"""Parámetros del negocio que se ajustan desde la pantalla de Configuración.

Los porcentajes se guardan como número de 0 a 100 (20 = 20%).
"""

from app.database.connection import get_connection

# Valores por omisión si la tabla todavía no tiene la clave
PARAMETROS = {
    "margen_minimo": {
        "valor": 20.0,
        "nombre": "Margen mínimo",
        "descripcion": "Margen de ganancia mínimo, sobre el precio de venta. "
                       "Define el precio mínimo de cada evento.",
    },
    "margen_objetivo": {
        "valor": 30.0,
        "nombre": "Margen objetivo",
        "descripcion": "Margen de ganancia objetivo, sobre el precio de venta. "
                       "Define el precio sugerido de cada evento.",
    },
    "margen_autorizacion": {
        "valor": 20.0,
        "nombre": "Margen que requiere autorización",
        "descripcion": "Si un vendedor cierra un precio con margen menor a este, "
                       "el evento queda pendiente de autorización de un director o admin.",
    },
}


def obtener_parametros(cur=None):
    """Diccionario clave -> valor (float, en %). Usa el cursor dado si viene."""
    propio = cur is None
    if propio:
        conn = get_connection()
        cur = conn.cursor()

    cur.execute("SELECT clave, valor FROM configuracion")
    guardados = {clave: float(valor) for clave, valor in cur.fetchall()}

    if propio:
        cur.close()
        conn.close()

    return {
        clave: guardados.get(clave, info["valor"])
        for clave, info in PARAMETROS.items()
    }


def obtener_configuracion():
    """Parámetros con nombre, descripción y última modificación."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT clave, valor, actualizado_en, actualizado_por
        FROM configuracion
    """)
    guardados = {fila[0]: fila for fila in cur.fetchall()}
    cur.close()
    conn.close()

    resultado = []
    for clave, info in PARAMETROS.items():
        fila = guardados.get(clave)
        resultado.append({
            "clave": clave,
            "nombre": info["nombre"],
            "descripcion": info["descripcion"],
            "valor": float(fila[1]) if fila else info["valor"],
            "actualizado_en": fila[2].isoformat(timespec="minutes") if fila and fila[2] else None,
            "actualizado_por": fila[3] if fila else None,
        })
    return resultado


def validar_parametros(valores):
    """Devuelve un mensaje de error, o None si los valores son coherentes."""
    minimo = valores["margen_minimo"]
    objetivo = valores["margen_objetivo"]
    autorizacion = valores["margen_autorizacion"]

    if not (0 <= minimo < 100 and 0 <= objetivo < 100 and 0 <= autorizacion < 100):
        return "Los márgenes deben estar entre 0 y 99.99%."
    if minimo > objetivo:
        return "El margen mínimo no puede ser mayor que el objetivo."
    if autorizacion > minimo:
        return ("El margen que requiere autorización no puede ser mayor que "
                "el mínimo: un precio dentro del rango permitido pediría autorización.")
    return None


def guardar_parametros(valores, usuario):
    """Guarda los parámetros y recalcula los precios de referencia de los eventos."""
    error = validar_parametros(valores)
    if error:
        return {"error": error}

    conn = get_connection()
    cur = conn.cursor()
    for clave, valor in valores.items():
        cur.execute("""
            INSERT INTO configuracion (clave, valor, descripcion, actualizado_en, actualizado_por)
            VALUES (%s, %s, %s, now(), %s)
            ON CONFLICT (clave) DO UPDATE
            SET valor = EXCLUDED.valor,
                actualizado_en = now(),
                actualizado_por = EXCLUDED.actualizado_por
        """, (clave, valor, PARAMETROS[clave]["descripcion"], usuario["nombre"]))

    cur.execute("SELECT id FROM eventos WHERE activo = TRUE")
    eventos = [fila[0] for fila in cur.fetchall()]
    conn.commit()
    cur.close()
    conn.close()

    # Precio mínimo y sugerido dependen de los márgenes: se recalculan.
    # Import local para no crear un ciclo con eventos_service.
    from app.services.eventos_service import actualizar_totales_evento
    for evento_id in eventos:
        actualizar_totales_evento(evento_id)

    return {
        "mensaje": "Configuración guardada",
        "eventos_recalculados": len(eventos),
    }
