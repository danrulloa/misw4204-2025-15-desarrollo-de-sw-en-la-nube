from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class VideoStatus(str, Enum):
    """Estados posibles de un video"""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class VideoUploadResponse(BaseModel):
    """Schema para la respuesta de upload de video"""
    message: str = Field(..., description="Mensaje de confirmación")
    video_id: str = Field(..., description="ID del video subido")
    task_id: str = Field(..., description="ID de la tarea de procesamiento")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Video subido correctamente. Procesamiento en curso.",
                "video_id": "a1b2c3d4",
                "task_id": "123456"
            }
        }


class VideoResponse(BaseModel):
    """Schema para la respuesta de información de un video"""
    video_id: str = Field(..., description="ID único del video")
    title: str = Field(..., description="Título del video")
    status: VideoStatus = Field(..., description="Estado del video")
    uploaded_at: datetime = Field(..., description="Fecha de subida")
    processed_at: Optional[datetime] = Field(None, description="Fecha de procesamiento")
    original_url: Optional[str] = Field(None, description="URL del video original")
    processed_url: Optional[str] = Field(None, description="URL del video procesado")
    votes: int = Field(default=0, description="Número de votos recibidos")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "a1b2c3d4",
                "title": "Tiros de tres en movimiento",
                "status": "processed",
                "uploaded_at": "2025-03-15T14:22:00Z",
                "processed_at": "2025-03-15T15:10:00Z",
                "original_url": "https://anb.com/uploads/a1b2c3d4.mp4",
                "processed_url": "https://anb.com/processed/a1b2c3d4.mp4",
                "votes": 125
            }
        }


class VideoListItemResponse(BaseModel):
    """Schema para un item en la lista de videos"""
    video_id: str = Field(..., description="ID único del video")
    title: str = Field(..., description="Título del video")
    status: VideoStatus = Field(..., description="Estado del video")
    uploaded_at: datetime = Field(..., description="Fecha de subida")
    processed_at: Optional[datetime] = Field(None, description="Fecha de procesamiento")
    processed_url: Optional[str] = Field(None, description="URL del video procesado")

    class Config:
        json_schema_extra = {
            "example": {
                "video_id": "123456",
                "title": "Mi mejor tiro de 3",
                "status": "processed",
                "uploaded_at": "2025-03-10T14:30:00Z",
                "processed_at": "2025-03-10T14:35:00Z",
                "processed_url": "https://anb.com/videos/processed/123456.mp4"
            }
        }


class VideoDeleteResponse(BaseModel):
    """Schema para la respuesta de eliminación de video"""
    message: str = Field(..., description="Mensaje de confirmación")
    video_id: str = Field(..., description="ID del video eliminado")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "El video ha sido eliminado exitosamente.",
                "video_id": "a1b2c3d4"
            }
        }
