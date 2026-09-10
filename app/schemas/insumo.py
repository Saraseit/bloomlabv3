from pydantic import BaseModel, Field


class InsumoCreate(BaseModel):
    nombre: str = Field(min_length=2)
    categoria_id: int
    unidad: str = Field(min_length=1)
    costo_referencia: float = Field(gt=0)
    # El usuario captura la merma como entero (10 = 10%).
    # La conversión a decimal (0.10) la hace insumos_service antes de insertar.
    porcentaje_merma: float = Field(ge=0, le=100)


class InsumoUpdate(BaseModel):
    nombre: str = Field(min_length=2)
    categoria_id: int
    unidad: str = Field(min_length=1)
    costo_referencia: float = Field(gt=0)
    # El usuario captura la merma como entero (10 = 10%).
    # La conversión a decimal (0.10) la hace insumos_service antes de actualizar.
    porcentaje_merma: float = Field(ge=0, le=100)
