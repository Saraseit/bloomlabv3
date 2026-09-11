from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_usuario_actual

from app.schemas.evento import (
    EventoCreate,
    EventoUpdate
)

from app.services.eventos_service import (
    obtener_eventos,
    crear_evento,
    actualizar_evento,
    eliminar_evento,
    obtener_evento,
    duplicar_evento
)

router = APIRouter(
    prefix="/eventos",
    tags=["Eventos"]
)


@router.get("")
def listar_eventos(usuario=Depends(get_usuario_actual)):

    return obtener_eventos()


@router.post("")
def nuevo_evento(data: EventoCreate, usuario=Depends(get_usuario_actual)):

    return crear_evento(data)

@router.put("/{evento_id}")
def editar_evento(
    evento_id: int,
    data: EventoUpdate,
    usuario=Depends(get_usuario_actual)
):

    return actualizar_evento(
        evento_id,
        data
    )

@router.delete("/{evento_id}")
def borrar_evento(evento_id: int, usuario=Depends(get_usuario_actual)):

    return eliminar_evento(evento_id)

@router.post("/{evento_id}/duplicar")
def clonar_evento(
    evento_id: int,
    usuario=Depends(get_usuario_actual)
):

    resultado = duplicar_evento(evento_id)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"]
        )

    return resultado


@router.get("/{evento_id}")
def detalle_evento(
    evento_id: int,
    usuario=Depends(get_usuario_actual)
):

    return obtener_evento(
        evento_id
    )