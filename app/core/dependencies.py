from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.security import decodificar_token
from app.database.connection import get_connection

bearer = HTTPBearer()


def get_usuario_actual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer)
) -> dict:
    token = credentials.credentials

    try:
        payload = decodificar_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    conn = get_connection()
    cur = conn.cursor()

    # Nunca se selecciona password_hash: no debe salir de la base
    cur.execute("""
        SELECT id, empresa_id, nombre, email, rol, activo
        FROM usuarios WHERE id = %s
    """, (payload.get("sub"),))

    fila = cur.fetchone()

    cur.close()
    conn.close()

    if not fila or not fila[5]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo"
        )

    return {
        "id": fila[0], "empresa_id": fila[1],
        "nombre": fila[2], "email": fila[3],
        "rol": fila[4]
    }


def require_admin(usuario=Depends(get_usuario_actual)):
    if usuario["rol"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol admin"
        )
    return usuario


def require_director_o_admin(usuario=Depends(get_usuario_actual)):
    if usuario["rol"] not in ("admin", "director"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol director o admin"
        )
    return usuario
