from pydantic import BaseModel, Field


class EventoCreate(BaseModel):

    cliente_id: int

    nombre: str

    tipo_evento: str | None = None

    fecha_evento: str | None = None

    lugar: str | None = None

    descripcion: str | None = None

    estatus: str | None = "Cotizacion"

    # Comisión del cliente para este evento, % sobre el precio de arreglos
    comision_porcentaje: float = Field(default=0, ge=0, lt=100)


class EventoUpdate(BaseModel):

    cliente_id: int

    nombre: str

    tipo_evento: str | None = None

    fecha_evento: str | None = None

    lugar: str | None = None

    descripcion: str | None = None

    estatus: str | None = None