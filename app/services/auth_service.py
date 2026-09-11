from app.database.connection import get_connection
from app.core.security import (
    hash_password, verify_password, crear_token
)
from datetime import datetime, timezone


def login(email: str, password: str) -> dict:

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, empresa_id, nombre, email,
               password_hash, rol, activo
        FROM usuarios WHERE email = %s
    """, (email.lower().strip(),))

    fila = cur.fetchone()

    # Igual que en cambiar_password: un hash ilegible se trata como
    # credencial incorrecta, no como error del servidor.
    try:
        credencial_valida = bool(fila) and verify_password(password, fila[4])
    except Exception:
        credencial_valida = False

    if not fila or not fila[6] or not credencial_valida:
        cur.close()
        conn.close()
        # Mismo mensaje para usuario inexistente y password incorrecta
        # (no revelar cuál de los dos falló)
        return {"error": "Credenciales incorrectas"}

    # Actualizar ultimo_acceso
    cur.execute("""
        UPDATE usuarios SET ultimo_acceso = %s WHERE id = %s
    """, (datetime.now(timezone.utc), fila[0]))

    conn.commit()

    cur.close()
    conn.close()

    token = crear_token({
        "sub": str(fila[0]),      # usuario id (el claim sub debe ser texto)
        "empresa_id": fila[1],
        "rol": fila[5],
        "nombre": fila[2]
    })

    return {
        "token": token,
        "usuario": {
            "id": fila[0], "nombre": fila[2],
            "email": fila[3], "rol": fila[5],
            "empresa_id": fila[1]
        }
    }
