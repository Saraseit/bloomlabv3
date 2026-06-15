from fastapi import APIRouter

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
def listar_insumos():
    return obtener_insumos()


@router.post("/insumos")
def nuevo_insumo(insumo: InsumoCreate):
    return crear_insumo(insumo)

from app.schemas.insumo import (
    InsumoCreate,
    InsumoUpdate
)

@router.put("/insumos/{insumo_id}")
def editar_insumo(
    insumo_id: int,
    insumo: InsumoUpdate
):
    return actualizar_insumo(
        insumo_id,
        insumo
    )


@router.delete("/insumos/{insumo_id}")
def borrar_insumo(insumo_id: int):
    return eliminar_insumo(insumo_id)

@router.get("/categorias")
def listar_categorias():

    return obtener_categorias_insumo()