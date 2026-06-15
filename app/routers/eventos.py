from fastapi import APIRouter

from app.schemas.evento import (
    EventoCreate,
    EventoUpdate
)

from app.services.eventos_service import (
    obtener_eventos,
    crear_evento,
    actualizar_evento,
    eliminar_evento,
    obtener_evento
)

router = APIRouter(
    prefix="/eventos",
    tags=["Eventos"]
)


@router.get("")
def listar_eventos():

    return obtener_eventos()


@router.post("")
def nuevo_evento(data: EventoCreate):

    return crear_evento(data)

@router.put("/{evento_id}")
def editar_evento(
    evento_id: int,
    data: EventoUpdate
):

    return actualizar_evento(
        evento_id,
        data
    )

@router.delete("/{evento_id}")
def borrar_evento(evento_id: int):

    return eliminar_evento(evento_id)

@router.get("/eventos/{evento_id}")
def detalle_evento(
    evento_id: int
):

    return obtener_evento(
        evento_id
    )