from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

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
def crear_detalle(data: ArregloDetalleCreate, usuario=Depends(get_usuario_actual)):

    return agregar_insumo_arreglo(data)

from app.services.arreglo_detalle_service import (
    agregar_insumo_arreglo,
    obtener_detalle_arreglo,
    editar_detalle
)
@router.get("/{arreglo_id}")
def listar_detalle(arreglo_id: int, usuario=Depends(get_usuario_actual)):

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
    data: ArregloDetalleUpdate,
    usuario=Depends(get_usuario_actual)
):

    return editar_detalle(
        detalle_id,
        data
    )

@router.delete("/{detalle_id}")
def borrar_detalle(detalle_id: int, usuario=Depends(get_usuario_actual)):

    return eliminar_detalle(detalle_id)