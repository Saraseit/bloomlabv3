from fastapi import APIRouter
from pydantic import BaseModel
from app.services.eventos_service import actualizar_totales_evento
from app.database.connection import get_connection

router = APIRouter()

class GastosEvento(BaseModel):
    costo_flete:   float = 0
    costo_montaje: float = 0

@router.put("/eventos/{evento_id}/gastos")
def actualizar_gastos(evento_id: int, data: GastosEvento):
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
def actualizar_precio_venta(evento_id: int, data: PrecioVenta):
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        UPDATE eventos
        SET precio_venta = %s
        WHERE id = %s
    """, (data.precio_venta, evento_id))

    conn.commit()
    cur.close()
    conn.close()

    return {"mensaje": "Precio de venta guardado"}