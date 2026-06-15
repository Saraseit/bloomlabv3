from pydantic import BaseModel, Field


class ClienteCreate(BaseModel):

    nombre: str

    telefono: str | None = None

    email: str | None = None

    empresa: str | None = None

    notas: str | None = None

    comision_porcentaje: float = 0


class ClienteUpdate(BaseModel):

    nombre: str = Field(min_length=2)

    telefono: str | None = None

    email: str | None = None

    empresa: str | None = None

    notas: str | None = None

    comision_porcentaje: float = 0
    