"""Interfaces para operaciones de consulta de videos."""

from typing import Protocol, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video


class VideoQueryServicePort(Protocol):
    """Define las operaciones disponibles para consultar videos."""

    async def list_user_videos(
        self,
        *,
        user_id: str,
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> List[Video]:
        """Obtiene los videos del usuario aplicando paginación."""
        ...

    async def get_user_video(
        self,
        *,
        user_id: str,
        video_id: str,
        db: AsyncSession,
    ) -> Video:
        """Obtiene un video del usuario o lanza HTTPException."""
        ...

    async def delete_user_video(
        self,
        *,
        user_id: str,
        video_id: str,
        db: AsyncSession,
    ) -> str:
        """Elimina un video del usuario devolviendo el id eliminado."""
        ...
