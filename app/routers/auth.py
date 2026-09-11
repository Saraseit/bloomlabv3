from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.usuario import (
    LoginRequest,
    CambioPassword
)

from app.core.dependencies import get_usuario_actual

from app.services.auth_service import login
from app.services.usuarios_service import cambiar_password

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


# Único endpoint público del sistema: sin Depends
@router.post("/login")
def iniciar_sesion(data: LoginRequest):

    resultado = login(data.email, data.password)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=resultado["error"],
            headers={"WWW-Authenticate": "Bearer"}
        )

    return resultado


@router.get("/me")
def usuario_actual(usuario=Depends(get_usuario_actual)):

    return usuario


@router.post("/cambiar-password")
def cambiar_mi_password(
    data: CambioPassword,
    usuario=Depends(get_usuario_actual)
):

    resultado = cambiar_password(usuario["id"], data)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado
