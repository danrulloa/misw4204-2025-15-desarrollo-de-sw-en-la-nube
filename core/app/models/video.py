"""
Modelo de Video
Almacena información de los videos subidos por los jugadores
Incluye estados de procesamiento y rutas de almacenamiento
"""
from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel
import enum


class VideoStatus(str, enum.Enum):
    """Estados posibles de un video durante su ciclo de vida"""
    uploaded = "uploaded"        # Recién subido, esperando procesamiento
    processing = "processing"    # En proceso de edición por el worker
    processed = "processed"      # Listo para votación pública
    failed = "failed"           # Error en el procesamiento


class Video(BaseModel):
    """
    Modelo de video
    Representa los videos de habilidades subidos por los jugadores
    """
    __tablename__ = "videos"
    
    # Relación con el usuario propietario
    user_id = Column(
        UUID(as_uuid=False), 
        ForeignKey("users.id", ondelete="CASCADE"),  # Si se borra el usuario, se borran sus videos
        nullable=False, 
        index=True
    )
    
    # Información del video
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    
    # Rutas de almacenamiento local (relativas a UPLOAD_DIR y PROCESSED_DIR)
    original_path = Column(String(500), nullable=False)      # Usado como input_path para el worker
    processed_path = Column(String(500), nullable=True)      # Se llena después del procesamiento
    
    # Estado y metadatos del video
    status = Column(
        Enum(VideoStatus), 
        default=VideoStatus.uploaded, 
        nullable=False, 
        index=True  # Índice para consultas de videos procesados
    )
    duration_seconds = Column(Integer, nullable=True)
    file_size_mb = Column(Float, nullable=True)
    
    # Timestamp de procesamiento
    processed_at = Column(DateTime, nullable=True)
    
    # Campo para trazabilidad con el worker (usado por David en RabbitMQ)
    correlation_id = Column(String(100), nullable=True, index=True)
    
    # Relaciones con otras tablas
    user = relationship("User", back_populates="videos")
    votes = relationship("Vote", back_populates="video", cascade="all, delete-orphan")

