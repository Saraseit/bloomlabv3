from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate
)

from app.services.clientes_service import (
    obtener_clientes,
    obtener_cliente_detalle,
    crear_cliente,
    actualizar_cliente,
    eliminar_cliente
)

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)


@router.get("")
def listar_clientes(usuario=Depends(get_usuario_actual)):

    return obtener_clientes()


@router.get("/{cliente_id}/detalle")
def detalle_cliente(cliente_id: int, usuario=Depends(get_usuario_actual)):

    return obtener_cliente_detalle(cliente_id)


@router.post("")
def nuevo_cliente(data: ClienteCreate, usuario=Depends(get_usuario_actual)):

    return crear_cliente(data)

@router.put("/{cliente_id}")
def editar_cliente(
    cliente_id: int,
    data: ClienteUpdate,
    usuario=Depends(get_usuario_actual)
):

    return actualizar_cliente(
        cliente_id,
        data
    )

@router.delete("/{cliente_id}")
def borrar_cliente(cliente_id: int, usuario=Depends(get_usuario_actual)):

    return eliminar_cliente(cliente_id)