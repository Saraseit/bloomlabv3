from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

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
    data: EventoArregloCreate,
    usuario=Depends(get_usuario_actual)
):

    return agregar_arreglo_evento(data)


@router.get("/{evento_id}")
def listar_detalle(
    evento_id: int,
    usuario=Depends(get_usuario_actual)
):

    return obtener_arreglos_evento(
        evento_id
    )

@router.put("/{detalle_id}")
def actualizar_detalle(
    detalle_id: int,
    data: EventoArregloUpdate,
    usuario=Depends(get_usuario_actual)
):

    return editar_arreglo_evento(
        detalle_id,
        data
    )

@router.delete("/{detalle_id}")
def borrar_detalle(
    detalle_id: int,
    usuario=Depends(get_usuario_actual)
):

    return eliminar_arreglo_evento(
        detalle_id
    )