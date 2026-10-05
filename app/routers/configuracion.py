from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_usuario_actual, require_director_o_admin
from app.services.configuracion_service import (
    obtener_configuracion,
    guardar_parametros
)

router = APIRouter(
    prefix="/configuracion",
    tags=["Configuración"]
)


class Parametros(BaseModel):
    margen_minimo: float = Field(ge=0, lt=100)
    margen_objetivo: float = Field(ge=0, lt=100)
    margen_autorizacion: float = Field(ge=0, lt=100)


@router.get("")
def ver_configuracion(usuario=Depends(get_usuario_actual)):
    """Cualquier usuario puede consultarla; solo director o admin la cambian."""
    return {
        "parametros": obtener_configuracion(),
        "puede_editar": usuario["rol"] in ("admin", "director"),
    }


@router.put("")
def editar_configuracion(
    data: Parametros,
    usuario=Depends(require_director_o_admin)
):
    resultado = guardar_parametros(data.model_dump(), usuario)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=resultado["error"]
        )

    return resultado
