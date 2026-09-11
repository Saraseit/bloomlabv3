from pydantic import BaseModel, Field


class EventoPagoCreate(BaseModel):

    fecha: str

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    metodo: str = "Transferencia"

    notas: str = ""


class EventoPagoUpdate(BaseModel):

    fecha: str

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    metodo: str

    notas: str = ""
