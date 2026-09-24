from pydantic import BaseModel, Field


class InsumoCreate(BaseModel):
    nombre: str = Field(min_length=2)
    categoria_id: int
    # Unidad de compra: cómo lo vende el proveedor ("Paquete 24", "Costal")
    unidad: str = Field(min_length=1)
    # Costo de UNA unidad de compra
    costo_referencia: float = Field(gt=0)
    # El usuario captura la merma como entero (10 = 10%).
    # La conversión a decimal (0.10) la hace insumos_service antes de insertar.
    porcentaje_merma: float = Field(ge=0, le=100)
    # Unidad de uso: cómo se captura en los arreglos ("tallo", "pieza").
    # Vacía = igual a la unidad de compra.
    unidad_uso: str | None = None
    # Unidades de uso que trae una unidad de compra (24 tallos por paquete)
    piezas_por_paquete: float = Field(default=1, gt=0)
    # True: en el evento se redondea a paquetes completos (perecederos).
    # False: se cobra solo la proporción usada (consumibles reutilizables).
    cobrar_paquete_completo: bool = False


class InsumoUpdate(InsumoCreate):
    pass
