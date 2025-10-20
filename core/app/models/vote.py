"""
Modelo de Voto
Registra los votos de usuarios por videos
Implementa regla de negocio: un usuario solo puede votar una vez por video
"""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Vote(BaseModel):
    """
    Modelo de voto
    Relaciona usuarios con videos para el sistema de votación pública
    """
    __tablename__ = "votes"
    
    # Referencias a usuario y video
    user_id = Column(String(64), nullable=False, index=True) 
    video_id = Column(
        UUID(as_uuid=False), 
        ForeignKey("videos.id", ondelete="CASCADE"),  # Si se borra el video, se borran sus votos
        nullable=False
    )
    
    # Relaciones ORM
    #user = relationship("User", back_populates="votes")
    video = relationship("Video", back_populates="votes")
    
    # Constraints e índices
    __table_args__ = (
        # Constraint: un usuario solo puede votar UNA vez por el mismo video
        UniqueConstraint('user_id', 'video_id', name='unique_user_video_vote'),
        # Índices para optimizar consultas de votos
        Index('idx_vote_user', 'user_id'),
        Index('idx_vote_video', 'video_id'),
    )

