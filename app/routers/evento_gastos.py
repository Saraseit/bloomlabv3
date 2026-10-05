from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_usuario_actual,
    require_director_o_admin
)
from pydantic import BaseModel, Field
from app.services.eventos_service import (
    actualizar_totales_evento,
    fijar_precio_venta,
    guardar_foto
)
from app.database.connection import get_connection

router = APIRouter()

# El margen bajo el cual un vendedor necesita autorización ya no es fijo:
# vive en Configuración (margen_autorizacion). Ver eventos_service.

class GastosEvento(BaseModel):
    costo_flete:   float = 0
    costo_montaje: float = 0

@router.put("/eventos/{evento_id}/gastos")
def actualizar_gastos(evento_id: int, data: GastosEvento, usuario=Depends(get_usuario_actual)):
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        UPDATE eventos
        SET
            costo_flete   = %s,
            costo_montaje = %s
        WHERE id = %s
    """, (data.costo_flete, data.costo_montaje, evento_id))

    conn.commit()
    cur.close()
    conn.close()

    # Recalcula todo con los nuevos gastos
    actualizar_totales_evento(evento_id)

    return {"mensaje": "Gastos actualizados"}

class PrecioVenta(BaseModel):
    precio_venta: float = Field(gt=0)

@router.put("/eventos/{evento_id}/precio-venta")
def actualizar_precio_venta(evento_id: int, data: PrecioVenta, usuario=Depends(get_usuario_actual)):
    # El margen se mide con la fórmula de margen (services/precios.py): la
    # comisión del cliente depende del precio, así que se recalcula con el
    # precio nuevo antes de decidir si hace falta autorización.
    resultado = fijar_precio_venta(evento_id, data.precio_venta, usuario)

    if "error" in resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=resultado["error"]
        )

    return resultado


# ── Autorización de precios por debajo del margen mínimo ──

class DecisionAutorizacion(BaseModel):
    decision: str
    nota: str = ""


@router.put("/eventos/{evento_id}/autorizacion")
def decidir_autorizacion(
    evento_id: int,
    data: DecisionAutorizacion,
    usuario=Depends(require_director_o_admin)
):

    if data.decision not in ("aprobar", "rechazar"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La decisión debe ser aprobar o rechazar"
        )

    conn = get_connection()
    cur  = conn.cursor()

    if data.decision == "aprobar":
        cur.execute("""
            UPDATE eventos
            SET
                estatus = 'Confirmado',
                nota_autorizacion = %s
            WHERE id = %s
            RETURNING id
        """, (f"Autorizado por {usuario['nombre']}", evento_id))
    else:
        # Al rechazar se borra el precio: el vendedor tiene que
        # renegociar y volver a capturarlo.
        cur.execute("""
            UPDATE eventos
            SET
                estatus = 'Cotizacion',
                precio_venta = NULL,
                nota_autorizacion = %s
            WHERE id = %s
            RETURNING id
        """, (data.nota, evento_id))

    resultado = cur.fetchone()

    conn.commit()
    cur.close()
    conn.close()

    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )

    # Al rechazar se borra el precio: ganancia y desglose vuelven a
    # medirse al precio sugerido.
    actualizar_totales_evento(evento_id)
    guardar_foto(
        evento_id,
        "autorizacion_aprobada" if data.decision == "aprobar" else "autorizacion_rechazada",
        usuario
    )

    return {
        "mensaje": "Evento aprobado" if data.decision == "aprobar"
                   else "Evento rechazado"
    }