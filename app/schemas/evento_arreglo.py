from pydantic import BaseModel


class EventoArregloCreate(BaseModel):

    evento_id: int

    arreglo_id: int

    cantidad: float

    observaciones: str | None = None


class EventoArregloUpdate(BaseModel):

    cantidad: float

    observaciones: str | None = None