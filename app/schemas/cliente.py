from pydantic import BaseModel, Field


class ClienteCreate(BaseModel):

    nombre: str

    telefono: str | None = None

    email: str | None = None

    empresa: str | None = None

    notas: str | None = None


# La comisión ya no es del cliente: se negocia por evento
# (eventos.comision_porcentaje). Si un navegador con la versión anterior
# la manda, Pydantic la ignora.


class ClienteUpdate(BaseModel):

    nombre: str = Field(min_length=2)

    telefono: str | None = None

    email: str | None = None

    empresa: str | None = None

    notas: str | None = None
    