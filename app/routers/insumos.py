from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.schemas.insumo import InsumoCreate
from app.services.insumos_service import (
    obtener_insumos,
    crear_insumo,
    actualizar_insumo,
    eliminar_insumo,
    obtener_categorias_insumo
)

router = APIRouter()


@router.get("/insumos")
def listar_insumos(usuario=Depends(get_usuario_actual)):
    return obtener_insumos()


@router.post("/insumos")
def nuevo_insumo(insumo: InsumoCreate, usuario=Depends(get_usuario_actual)):
    return crear_insumo(insumo)

from app.schemas.insumo import (
    InsumoCreate,
    InsumoUpdate
)

@router.put("/insumos/{insumo_id}")
def editar_insumo(
    insumo_id: int,
    insumo: InsumoUpdate,
    usuario=Depends(get_usuario_actual)
):
    return actualizar_insumo(
        insumo_id,
        insumo
    )


@router.delete("/insumos/{insumo_id}")
def borrar_insumo(insumo_id: int, usuario=Depends(get_usuario_actual)):
    return eliminar_insumo(insumo_id)

@router.get("/categorias")
def listar_categorias(usuario=Depends(get_usuario_actual)):

    return obtener_categorias_insumo()