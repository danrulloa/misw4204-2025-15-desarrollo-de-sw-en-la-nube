"""Implementaciones concretas del servicio de videos."""

from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoStatus
from app.services.storage.utils import abs_storage_path
from app.services.videos.base import VideoQueryServicePort


class VideoQueryService(VideoQueryServicePort):
    """Servicio que consulta y gestiona videos usando SQLAlchemy."""

    async def list_user_videos(
        self,
        *,
        user_id: str,
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> List[Video]:
        stmt = (
            select(Video)
            .where(Video.user_id == user_id)
            .order_by(Video.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_user_video(
        self,
        *,
        user_id: str,
        video_id: str,
        db: AsyncSession,
    ) -> Video:
        stmt = select(Video).where(Video.id == video_id)
        result = await db.execute(stmt)
        video = result.scalar_one_or_none()
        if not video:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        if str(video.user_id) != str(user_id):
            raise HTTPException(status_code=403, detail="El video no pertenece al usuario")
        return video

    async def delete_user_video(
        self,
        *,
        user_id: str,
        video_id: str,
        db: AsyncSession,
    ) -> str:
        video = await self.get_user_video(user_id=user_id, video_id=video_id, db=db)
        video_id_str = str(video.id)

        if video.status == VideoStatus.processed:
            raise HTTPException(
                status_code=400,
                detail="El video ya está listo para votación; no puede eliminarse.",
            )

        # Eliminar archivos asociados (si existen). Ignorar errores individuales.
        try:
            if video.original_path:
                p = abs_storage_path(video.original_path)
                if p.is_file():
                    p.unlink(missing_ok=True)
            if video.processed_path:
                p = abs_storage_path(video.processed_path)
                if p.is_file():
                    p.unlink(missing_ok=True)
        except Exception:
            pass

        await db.delete(video)
        await db.commit()
        return video_id_str
