"""
Handlers globales para excepciones FastAPI
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.exceptions.custom_exceptions import APIException
import logging

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handler para excepciones personalizadas de la API
    
    Args:
        request: Request de FastAPI
        exc: Excepción personalizada
        
    Returns:
        JSONResponse con el error formateado
    """
    logger.error(f"API Exception: {exc.message} - Status: {exc.status_code}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.error_code
        }
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler para errores de validación de Pydantic
    
    Args:
        request: Request de FastAPI
        exc: Error de validación
        
    Returns:
        JSONResponse con los errores de validación
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Error de validación",
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors()
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler para excepciones no controladas
    
    Args:
        request: Request de FastAPI
        exc: Excepción genérica
        
    Returns:
        JSONResponse con error genérico
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Error interno del servidor",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )
