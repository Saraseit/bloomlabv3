from fastapi import APIRouter, Depends

from app.core.dependencies import get_usuario_actual

from app.services.reportes_service import (
    resumen_general,
    eventos_por_mes,
    top_clientes,
    top_arreglos,
    rentabilidad_por_evento
)

# Distinto de routers/reportes.py, que genera los PDFs del evento.
router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"]
)


@router.get("/resumen")
def reporte_resumen(usuario=Depends(get_usuario_actual)):

    return resumen_general()


@router.get("/eventos-por-mes")
def reporte_eventos_por_mes(usuario=Depends(get_usuario_actual)):

    return eventos_por_mes()


@router.get("/top-clientes")
def reporte_top_clientes(usuario=Depends(get_usuario_actual)):

    return top_clientes(10)


@router.get("/top-arreglos")
def reporte_top_arreglos(usuario=Depends(get_usuario_actual)):

    return top_arreglos(10)


@router.get("/rentabilidad")
def reporte_rentabilidad(usuario=Depends(get_usuario_actual)):

    return rentabilidad_por_evento()
