from fastapi import APIRouter

from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate
)

from app.services.clientes_service import (
    obtener_clientes,
    crear_cliente,
    actualizar_cliente,
    eliminar_cliente
)

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.get("")
def listar_clientes():

    return obtener_clientes()


@router.post("")
def nuevo_cliente(data: ClienteCreate):

    return crear_cliente(data)

@router.put("/{cliente_id}")
def editar_cliente(
    cliente_id: int,
    data: ClienteUpdate
):

    return actualizar_cliente(
        cliente_id,
        data
    )

@router.delete("/{cliente_id}")
def borrar_cliente(cliente_id: int):

    return eliminar_cliente(cliente_id)