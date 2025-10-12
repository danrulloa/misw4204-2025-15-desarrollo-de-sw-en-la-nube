from pydantic import BaseModel, Field
from typing import Optional, Any


class ErrorResponse(BaseModel):
    """Schema estándar para respuestas de error"""
    detail: str = Field(..., description="Descripción del error")
    error_code: Optional[str] = Field(None, description="Código de error específico")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "El recurso solicitado no fue encontrado",
                "error_code": "RESOURCE_NOT_FOUND"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Schema para errores de validación"""
    detail: str = Field(..., description="Descripción del error")
    errors: list[dict[str, Any]] = Field(..., description="Lista de errores de validación")

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Error de validación",
                "errors": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ]
            }
        }


class MessageResponse(BaseModel):
    """Schema genérico para respuestas con mensaje"""
    message: str = Field(..., description="Mensaje de respuesta")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operación completada exitosamente"
            }
        }
