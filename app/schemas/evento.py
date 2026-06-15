from pydantic import BaseModel


class EventoCreate(BaseModel):

    cliente_id: int

    nombre: str

    fecha_evento: str | None = None

    lugar: str | None = None

    descripcion: str | None = None

    estatus: str | None = "Cotizacion"


class EventoUpdate(BaseModel):

    cliente_id: int

    nombre: str

    fecha_evento: str | None = None

    lugar: str | None = None

    descripcion: str | None = None

    estatus: str | None = None