from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.schemas.evento_pago import (
    EventoPagoCreate,
    EventoPagoUpdate
)

from app.services.evento_pagos_service import (
    obtener_pagos_evento,
    agregar_pago,
    editar_pago,
    eliminar_pago,
    calcular_resumen_pagos
)

router = APIRouter(
    tags=["Evento Pagos"]
)


# /resumen va antes que las rutas con {pago_id}
# para que no lo capture un parámetro de ruta.
@router.get("/eventos/{evento_id}/pagos/resumen")
def resumen_pagos(evento_id: int, usuario=Depends(get_usuario_actual)):

    return calcular_resumen_pagos(evento_id)


@router.get("/eventos/{evento_id}/pagos")
def listar_pagos(evento_id: int, usuario=Depends(get_usuario_actual)):

    return obtener_pagos_evento(evento_id)


@router.post("/eventos/{evento_id}/pagos")
def nuevo_pago(
    evento_id: int,
    data: EventoPagoCreate,
    usuario=Depends(get_usuario_actual)
):

    return agregar_pago(
        evento_id,
        data
    )


@router.put("/eventos/{evento_id}/pagos/{pago_id}")
def actualizar_pago(
    evento_id: int,
    pago_id: int,
    data: EventoPagoUpdate,
    usuario=Depends(get_usuario_actual)
):

    return editar_pago(
        pago_id,
        data
    )


@router.delete("/eventos/{evento_id}/pagos/{pago_id}")
def borrar_pago(
    evento_id: int,
    pago_id: int,
    usuario=Depends(get_usuario_actual)
):

    return eliminar_pago(pago_id)
