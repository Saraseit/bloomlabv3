from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.services.compras_service import obtener_plan_compras

router = APIRouter(
    tags=["Evento Lista de Compras"]
)


@router.get("/eventos/{evento_id}/plan-compras")
def plan_compras(evento_id: int, usuario=Depends(get_usuario_actual)):
    """Insumos planeados del evento (redondeados a paquete) vs comprados."""

    return obtener_plan_compras(evento_id)
