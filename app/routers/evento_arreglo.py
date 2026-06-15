from fastapi import APIRouter

from app.schemas.evento_arreglo import (
    EventoArregloCreate,
    EventoArregloUpdate
)

from app.services.evento_arreglo_service import (
    agregar_arreglo_evento,
    obtener_arreglos_evento,
    editar_arreglo_evento,
    eliminar_arreglo_evento
)

router = APIRouter(
    prefix="/evento-arreglos",
    tags=["Evento Arreglos"]
)


@router.post("")
def crear_detalle(
    data: EventoArregloCreate
):

    return agregar_arreglo_evento(data)


@router.get("/{evento_id}")
def listar_detalle(
    evento_id: int
):

    return obtener_arreglos_evento(
        evento_id
    )

@router.put("/{detalle_id}")
def actualizar_detalle(
    detalle_id: int,
    data: EventoArregloUpdate
):

    return editar_arreglo_evento(
        detalle_id,
        data
    )

@router.delete("/{detalle_id}")
def borrar_detalle(
    detalle_id: int
):

    return eliminar_arreglo_evento(
        detalle_id
    )