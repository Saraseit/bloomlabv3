from pydantic import BaseModel, Field


class EventoGastoRealCreate(BaseModel):

    fecha: str

    categoria: str = Field(min_length=2)

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    es_reembolsable: bool = False

    notas: str = ""

    # Opcional: liga el gasto a un insumo para la lista planeado vs comprado
    insumo_id: int | None = None

    paquetes_comprados: float | None = Field(default=None, ge=0)


class EventoGastoRealUpdate(BaseModel):

    fecha: str

    categoria: str = Field(min_length=2)

    concepto: str = Field(min_length=2)

    monto: float = Field(gt=0)

    es_reembolsable: bool = False

    notas: str = ""

    # Opcional: liga el gasto a un insumo para la lista planeado vs comprado
    insumo_id: int | None = None

    paquetes_comprados: float | None = Field(default=None, ge=0)
