from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_usuario_actual,
    require_director_o_admin
)
from pydantic import BaseModel
from app.services.eventos_service import actualizar_totales_evento
from app.database.connection import get_connection

router = APIRouter()

# Por debajo de este margen, un vendedor no puede cerrar el precio solo:
# el evento queda pendiente de que lo autorice un director o un admin.
MARGEN_AUTORIZACION = 0.25

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
    precio_venta: float

@router.put("/eventos/{evento_id}/precio-venta")
def actualizar_precio_venta(evento_id: int, data: PrecioVenta, usuario=Depends(get_usuario_actual)):
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT costo_final
        FROM eventos
        WHERE id = %s
    """, (evento_id,))

    fila = cur.fetchone()

    if not fila:
        cur.close()
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado"
        )

    costo_final = float(fila[0] or 0)

    # Con precio en cero no hay margen que calcular; se trata como 0%
    # para que caiga del lado que requiere autorización.
    if data.precio_venta > 0:
        margen = 1 - (costo_final / data.precio_venta)
    else:
        margen = 0.0

    requiere_autorizacion = (
        margen < MARGEN_AUTORIZACION
        and usuario["rol"] == "vendedor"
    )

    if requiere_autorizacion:
        cur.execute("""
            UPDATE eventos
            SET
                precio_venta = %s,
                estatus = 'Pendiente Autorización'
            WHERE id = %s
        """, (data.precio_venta, evento_id))
    else:
        cur.execute("""
            UPDATE eventos
            SET precio_venta = %s
            WHERE id = %s
        """, (data.precio_venta, evento_id))

    conn.commit()
    cur.close()
    conn.close()

    return {
        "mensaje": "Precio guardado",
        "requiere_autorizacion": requiere_autorizacion,
        "margen": round(margen * 100, 2)
    }


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

    return {
        "mensaje": "Evento aprobado" if data.decision == "aprobar"
                   else "Evento rechazado"
    }