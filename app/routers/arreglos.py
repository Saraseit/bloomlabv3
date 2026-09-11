from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.schemas.arreglo import (
    ArregloCreate,
    ArregloUpdate
)
from app.services.arreglos_service import (
    obtener_arreglos,
    obtener_arreglo,
    crear_arreglo,
    editar_arreglo,
    eliminar_arreglo
)

router = APIRouter(
    prefix="/arreglos",
    tags=["Arreglos"]
)


@router.get("")
def listar_arreglos(usuario=Depends(get_usuario_actual)):

    return obtener_arreglos()

@router.get("/{arreglo_id}")
def obtener_un_arreglo(arreglo_id: int, usuario=Depends(get_usuario_actual)):

    return obtener_arreglo(arreglo_id)


@router.post("")
def nuevo_arreglo(data: ArregloCreate, usuario=Depends(get_usuario_actual)):

    return crear_arreglo(data)


@router.put("/{arreglo_id}")
def actualizar_arreglo(
    arreglo_id: int,
    data: ArregloUpdate,
    usuario=Depends(get_usuario_actual)
):

    return editar_arreglo(
        arreglo_id,
        data
    )

@router.delete("/{arreglo_id}")
def borrar_arreglo(arreglo_id: int, usuario=Depends(get_usuario_actual)):

    return eliminar_arreglo(arreglo_id)