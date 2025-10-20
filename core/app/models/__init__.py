"""
Módulo de modelos de base de datos
Exporta todos los modelos para fácil importación en otros módulos
"""
from app.models.video import Video, VideoStatus
from app.models.vote import Vote

__all__ = ["Video", "VideoStatus", "Vote"]

