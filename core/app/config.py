from pydantic_settings import BaseSettings
from typing import List
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
    
    # Rutas de almacenamiento
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR","/app/storage/uploads")
    PROCESSED_DIR: str = os.getenv("PROCESSED_DIR","/app/storage/processed")

    # Configuración de base de datos
    DATABASE_URL: str = "postgresql+asyncpg://anb_user:anb_pass@anb-core-db:5432/anb_core"

    
    VIDEO_EXCHANGE: str = os.getenv("VIDEO_EXCHANGE", "video")
    WORKER_INPUT_PREFIX: str = "/mnt/uploads"
    STORAGE_BACKEND: str = "local"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
