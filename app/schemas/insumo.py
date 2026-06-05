from pydantic import BaseModel, Field


class InsumoCreate(BaseModel):
    nombre: str = Field(min_length=2)
    categoria_id: int
    unidad: str = Field(min_length=1)
    costo_referencia: float = Field(gt=0)
    porcentaje_merma: float = Field(ge=0, le=1)


class InsumoUpdate(BaseModel):
    nombre: str = Field(min_length=2)
    categoria_id: int
    unidad: str = Field(min_length=1)
    costo_referencia: float = Field(gt=0)
    porcentaje_merma: float = Field(ge=0, le=1)