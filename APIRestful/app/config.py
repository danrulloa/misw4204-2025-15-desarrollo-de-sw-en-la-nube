from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Literal
import os


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Información de la aplicación
    APP_NAME: str = "ANB Rising Stars API"
    DEBUG: bool = False
    API_VERSION: str = "v1"
    
    # Configuración de archivos
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_VIDEO_FORMATS: List[str] = ["mp4", "avi", "mov"]
    MIN_VIDEO_DURATION_SECONDS: int = 20
    MAX_VIDEO_DURATION_SECONDS: int = 60
    UPLOAD_DIR: str = "uploads"
    PROCESSED_DIR: str = "processed"

    STORAGE_BACKEND: Literal["local", "s3"] = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()

ALLOWED_VIDEO_FORMATS = settings.ALLOWED_VIDEO_FORMATS
MAX_UPLOAD_SIZE_MB   = settings.MAX_UPLOAD_SIZE_MB 
STORAGE_BACKEND      = settings.STORAGE_BACKEND
UPLOAD_DIR           = settings.UPLOAD_DIR
PROCESSED_DIR        = settings.PROCESSED_DIR
