from pydantic import BaseModel

class ArregloCreate(BaseModel):

    nombre: str

    categoria: str

    descripcion: str | None = None

    imagen_url: str | None = None


from pydantic import BaseModel

class ArregloUpdate(BaseModel):

    nombre: str

    categoria: str | None = None

    descripcion: str | None = None

    imagen_url: str | None = None


