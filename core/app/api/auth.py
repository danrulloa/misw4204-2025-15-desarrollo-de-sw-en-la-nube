"""
Router de autenticación
Endpoints para signup y login
"""

from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/auth", tags=["Auth"])


class SignupRequest(BaseModel):
    first_name: str = Field(..., description="Nombre del usuario")
    last_name: str = Field(..., description="Apellido del usuario")
    email: str = Field(..., description="Email del usuario")
    password1: str = Field(..., description="Contraseña")
    password2: str = Field(..., description="Confirmación de contraseña")
    city: str = Field(..., description="Ciudad del usuario")
    country: str = Field(..., description="País del usuario")


class LoginRequest(BaseModel):
    email: str = Field(..., description="Email del usuario")
    password: str = Field(..., description="Contraseña")


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    summary="Registro de usuario",
    description="Registra un nuevo usuario en el sistema"
)
async def signup(request: SignupRequest):
    """Registra un nuevo usuario"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión",
    description="Autentica un usuario y retorna un token"
)
async def login(request: LoginRequest):
    """Inicia sesión de usuario"""
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented yet")

