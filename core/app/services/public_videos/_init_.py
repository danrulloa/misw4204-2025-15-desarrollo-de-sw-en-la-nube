from functools import lru_cache

from app.services.public_videos.base import PublicVideoServicePort
from app.services.public_videos.local import PublicVideoService


@lru_cache(maxsize=1)
def get_public_video_service() -> PublicVideoServicePort:
    return PublicVideoService()
