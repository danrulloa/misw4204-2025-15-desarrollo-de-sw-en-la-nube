"""
Router de autenticación
Endpoints para registro y login de usuarios
"""

from fastapi import APIRouter, status, HTTPException
from app.schemas.auth import (
    UserSignupRequest,
    UserSignupResponse,
    UserLoginRequest,
    TokenResponse
)
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=UserSignupResponse,
    summary="Registro de jugadores",
    description="Permite a un nuevo jugador registrarse en la plataforma ANB Rising Stars",
    responses={
        201: {
            "description": "Usuario creado exitosamente",
            "model": UserSignupResponse
        },
        400: {
            "description": "Error de validación (email duplicado, contraseñas no coinciden)",
            "model": ErrorResponse
        }
    }
)
async def signup(user_data: UserSignupRequest) -> UserSignupResponse:
    """
    Registra un nuevo jugador en la plataforma.
    
    Validaciones:
    - Email único
    - Contraseñas coinciden (password1 == password2)
    - Todos los campos requeridos
    """
    # TODO: Implementar cuando se tenga DB y auth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
    summary="Inicio de sesión",
    description="Autentica un usuario y genera un token JWT",
    responses={
        200: {
            "description": "Autenticación exitosa, retorna token JWT",
            "model": TokenResponse
        },
        401: {
            "description": "Credenciales inválidas",
            "model": ErrorResponse
        }
    }
)
async def login(credentials: UserLoginRequest) -> TokenResponse:
    """
    Autentica un usuario con email y contraseña.
    
    Retorna un token JWT que debe ser incluido en el header Authorization
    de las siguientes peticiones: Bearer {token}
    """
    # TODO: Implementar cuando se tenga DB y Keycloak
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando integración con Keycloak."
    )
