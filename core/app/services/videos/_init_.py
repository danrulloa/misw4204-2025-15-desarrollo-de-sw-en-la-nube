"""Factories para servicios de videos."""

from app.services.videos.base import VideoQueryServicePort
from app.services.videos.local import VideoQueryService


def get_video_query_service() -> VideoQueryServicePort:
    return VideoQueryService()

