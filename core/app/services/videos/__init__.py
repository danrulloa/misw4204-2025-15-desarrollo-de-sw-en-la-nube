"""Servicios relacionados con consultas de videos."""

from app.services.videos.base import VideoQueryServicePort
from app.services.videos._init_ import get_video_query_service

__all__ = ["VideoQueryServicePort", "get_video_query_service"]

