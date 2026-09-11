from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    ResetPasswordAdmin
)

from app.core.dependencies import require_admin

from app.services.usuarios_service import (
    obtener_usuarios,
    crear_usuario,
    actualizar_usuario,
    resetear_password,
    eliminar_usuario
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


@router.get("")
def listar_usuarios(usuario=Depends(require_admin)):

    return obtener_usuarios(usuario["empresa_id"])


@router.post("")
def nuevo_usuario(
    data: UsuarioCreate,
    usuario=Depends(require_admin)
):

    resultado = crear_usuario(data, usuario["empresa_id"])

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado


@router.put("/{usuario_id}")
def editar_usuario(
    usuario_id: int,
    data: UsuarioUpdate,
    usuario=Depends(require_admin)
):

    resultado = actualizar_usuario(usuario_id, data)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado


@router.post("/{usuario_id}/reset-password")
def reset_password_admin(
    usuario_id: int,
    data: ResetPasswordAdmin,
    usuario=Depends(require_admin)
):

    # La propia contraseña se cambia por el otro endpoint, que sí pide
    # la vigente; aquí se evita que un admin se la reinicie sin saberla.
    if usuario_id == usuario["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usa /auth/cambiar-password para cambiar tu propia contraseña"
        )

    resultado = resetear_password(usuario_id, data.nueva_password)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado


@router.delete("/{usuario_id}")
def borrar_usuario(
    usuario_id: int,
    usuario=Depends(require_admin)
):

    resultado = eliminar_usuario(usuario_id, usuario["id"])

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado
