from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

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
    duplicar_evento,
    actualizar_comision,
    guardar_foto,
    listar_fotos,
    obtener_foto
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
        data,
        usuario
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


class ComisionEvento(BaseModel):
    comision_porcentaje: float


@router.put("/{evento_id}/comision")
def editar_comision(
    evento_id: int,
    data: ComisionEvento,
    usuario=Depends(get_usuario_actual)
):
    """Comisión del cliente para este evento (% sobre el precio de arreglos)."""

    resultado = actualizar_comision(evento_id, data.comision_porcentaje, usuario)

    if "error" in resultado:
        codigo = (status.HTTP_404_NOT_FOUND if resultado["error"] == "Evento no encontrado"
                  else status.HTTP_400_BAD_REQUEST)
        raise HTTPException(status_code=codigo, detail=resultado["error"])

    return resultado


# ── Fotografías de la cotización (para reportes) ──

@router.get("/{evento_id}/fotos")
def fotos_evento(evento_id: int, usuario=Depends(get_usuario_actual)):
    """Fotografías guardadas del evento, la más reciente primero."""
    return listar_fotos(evento_id)


@router.post("/{evento_id}/fotos")
def nueva_foto(evento_id: int, usuario=Depends(get_usuario_actual)):
    """Guarda a mano el estado actual de la cotización."""
    foto_id = guardar_foto(evento_id, "manual", usuario)
    if foto_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Evento no encontrado")
    return {"mensaje": "Fotografía guardada", "id": foto_id}


@router.get("/{evento_id}/fotos/{foto_id}")
def foto_evento(evento_id: int, foto_id: int, usuario=Depends(get_usuario_actual)):
    """Una fotografía con el desglose de sus partidas."""
    foto = obtener_foto(evento_id, foto_id)
    if foto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Fotografía no encontrada")
    return foto


@router.get("/{evento_id}")
def detalle_evento(
    evento_id: int,
    usuario=Depends(get_usuario_actual)
):

    return obtener_evento(
        evento_id
    )