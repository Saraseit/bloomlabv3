from fastapi import APIRouter

from app.schemas.arreglo_detalle import (
    ArregloDetalleCreate
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
    obtener_detalle_arreglo
)
@router.get("/{arreglo_id}")
def listar_detalle(arreglo_id: int):

    return obtener_detalle_arreglo(arreglo_id)