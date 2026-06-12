from fastapi import APIRouter

from app.schemas.arreglo_detalle import (
    ArregloDetalleCreate,
    ArregloDetalleUpdate
)
from app.services.arreglo_detalle_service import (
    agregar_insumo_arreglo
)

router = APIRouter(
    prefix="/arreglo-detalle",
    tags=["Arreglo Detalle"]
)


@router.post("")
def crear_detalle(data: ArregloDetalleCreate):

    return agregar_insumo_arreglo(data)

from app.services.arreglo_detalle_service import (
    agregar_insumo_arreglo,
    obtener_detalle_arreglo,
    editar_detalle
)
@router.get("/{arreglo_id}")
def listar_detalle(arreglo_id: int):

    return obtener_detalle_arreglo(arreglo_id)

from app.services.arreglo_detalle_service import (
    agregar_insumo_arreglo,
    obtener_detalle_arreglo,
    editar_detalle,
    eliminar_detalle
)
@router.put("/{detalle_id}")
def actualizar_detalle(
    detalle_id: int,
    data: ArregloDetalleUpdate
):

    return editar_detalle(
        detalle_id,
        data
    )

@router.delete("/{detalle_id}")
def borrar_detalle(detalle_id: int):

    return eliminar_detalle(detalle_id)