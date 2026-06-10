from fastapi import APIRouter

from app.schemas.arreglo import ArregloCreate

from app.services.arreglos_service import (
    obtener_arreglos,
    crear_arreglo
)

router = APIRouter(
    prefix="/arreglos",
    tags=["Arreglos"]
)


@router.get("")
def listar_arreglos():

    return obtener_arreglos()


@router.post("")
def nuevo_arreglo(data: ArregloCreate):

    return crear_arreglo(data)