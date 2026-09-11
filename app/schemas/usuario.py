from pydantic import BaseModel, Field, EmailStr


class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(min_length=6)


class UsuarioCreate(BaseModel):

    nombre: str = Field(min_length=2)

    email: EmailStr

    password: str = Field(min_length=8)

    rol: str = Field(default="vendedor",
                     pattern="^(admin|vendedor|director)$")


class UsuarioUpdate(BaseModel):

    nombre: str = Field(min_length=2)

    email: EmailStr

    rol: str = Field(pattern="^(admin|vendedor|director)$")

    activo: bool = True


class CambioPassword(BaseModel):

    password_actual: str

    password_nuevo: str = Field(min_length=8)
