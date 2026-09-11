from fastapi import APIRouter

from app.schemas.evento_gasto_real import (
    EventoGastoRealCreate,
    EventoGastoRealUpdate
)

from app.services.evento_gastos_reales_service import (
    obtener_gastos_reales,
    agregar_gasto_real,
    editar_gasto_real,
    eliminar_gasto_real,
    calcular_resumen_gastos_reales
)

router = APIRouter(
    tags=["Evento Gastos Reales"]
)


# /resumen va antes que las rutas con {gasto_id}
# para que no lo capture un parámetro de ruta.
@router.get("/eventos/{evento_id}/gastos-reales/resumen")
def resumen_gastos_reales(evento_id: int):

    return calcular_resumen_gastos_reales(evento_id)


@router.get("/eventos/{evento_id}/gastos-reales")
def listar_gastos_reales(evento_id: int):

    return obtener_gastos_reales(evento_id)


@router.post("/eventos/{evento_id}/gastos-reales")
def nuevo_gasto_real(
    evento_id: int,
    data: EventoGastoRealCreate
):

    return agregar_gasto_real(
        evento_id,
        data
    )


@router.put("/eventos/{evento_id}/gastos-reales/{gasto_id}")
def actualizar_gasto_real(
    evento_id: int,
    gasto_id: int,
    data: EventoGastoRealUpdate
):

    return editar_gasto_real(
        gasto_id,
        data
    )


@router.delete("/eventos/{evento_id}/gastos-reales/{gasto_id}")
def borrar_gasto_real(
    evento_id: int,
    gasto_id: int
):

    return eliminar_gasto_real(gasto_id)
