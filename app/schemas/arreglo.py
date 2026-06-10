from pydantic import BaseModel

class ArregloCreate(BaseModel):

    nombre: str

    categoria: str

    descripcion: str | None = None