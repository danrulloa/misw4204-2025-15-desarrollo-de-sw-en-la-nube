from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSignupRequest(BaseModel):
    """Schema para el registro de nuevos jugadores"""
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombre del jugador")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellido del jugador")
    email: EmailStr = Field(..., description="Correo electrónico único")
    password1: str = Field(..., min_length=8, description="Contraseña")
    password2: str = Field(..., min_length=8, description="Confirmación de contraseña")
    city: str = Field(..., min_length=1, max_length=100, description="Ciudad del jugador")
    country: str = Field(..., min_length=1, max_length=100, description="País del jugador")

    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "password1": "StrongPass123",
                "password2": "StrongPass123",
                "city": "Bogotá",
                "country": "Colombia"
            }
        }


class UserLoginRequest(BaseModel):
    """Schema para el inicio de sesión"""
    email: EmailStr = Field(..., description="Correo electrónico")
    password: str = Field(..., description="Contraseña")

    @field_validator('email')
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "StrongPass123"
            }
        }


class TokenResponse(BaseModel):
    """Schema para la respuesta de autenticación"""
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field(default="Bearer", description="Tipo de token")
    expires_in: int = Field(default=3600, description="Tiempo de expiración en segundos")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
                "token_type": "Bearer",
                "expires_in": 3600
            }
        }


class UserSignupResponse(BaseModel):
    """Schema para la respuesta de registro exitoso"""
    message: str = Field(..., description="Mensaje de confirmación")
    user_id: int = Field(..., description="ID del usuario creado")
    email: str = Field(..., description="Email del usuario")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Usuario creado exitosamente",
                "user_id": 1,
                "email": "john@example.com"
            }
        }
