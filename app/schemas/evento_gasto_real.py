from pydantic import BaseModel, Field


class EventoGastoRealCreate(BaseModel):

    fecha: str

    categoria: str = Field(min_length=2)

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    es_reembolsable: bool = False

    notas: str = ""


class EventoGastoRealUpdate(BaseModel):

    fecha: str

    categoria: str = Field(min_length=2)

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    es_reembolsable: bool = False

    notas: str = ""
