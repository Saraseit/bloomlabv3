from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate
)

from app.core.dependencies import require_admin

from app.services.usuarios_service import (
    obtener_usuarios,
    crear_usuario,
    actualizar_usuario,
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
