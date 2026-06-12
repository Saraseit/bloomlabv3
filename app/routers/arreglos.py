from fastapi import APIRouter

from app.schemas.arreglo import ArregloCreate

from app.services.arreglos_service import (
    obtener_arreglos,
    obtener_arreglo,
    crear_arreglo
)

router = APIRouter(
    prefix="/arreglos",
    tags=["Arreglos"]
)


@router.get("")
def listar_arreglos():

    return obtener_arreglos()

@router.get("/{arreglo_id}")
def obtener_un_arreglo(arreglo_id: int):

    return obtener_arreglo(arreglo_id)


@router.post("")
def nuevo_arreglo(data: ArregloCreate):

    return crear_arreglo(data)