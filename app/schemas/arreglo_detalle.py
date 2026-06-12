from pydantic import BaseModel

class ArregloDetalleCreate(BaseModel):

    arreglo_id: int

    insumo_id: int

    cantidad: float

    costo_real: float

    observaciones: str | None = None

class ArregloDetalleUpdate(BaseModel):

    cantidad: float

    costo_real: float

    observaciones: str | None = None