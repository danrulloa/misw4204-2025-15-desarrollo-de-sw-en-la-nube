import os
import uuid
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.video import Video, VideoStatus
from app.services.storage._init_ import get_storage
from app.services.mq.rabbit import RabbitPublisher


class LocalUploadService:
    """Implementación local del servicio de subida de videos.

    Encapsula la validación, almacenamiento, persistencia y publicación a MQ.
    """

    async def upload(
        self,
        *,
        user_id: str,
        title: str,
        upload_file: UploadFile,
        user_info: Dict[str, str],
        db: AsyncSession,
    ) -> Tuple[Video, str]:
        ext, size_bytes = self._validate_ext_and_size(upload_file)

        storage = get_storage()
        filename = f"{uuid.uuid4().hex}.{ext}"
        try:
            saved_rel_path = storage.save(
                upload_file.file,
                filename,
                upload_file.content_type or "application/octet-stream",
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Error guardando archivo en storage: {e}")

        video = Video(
            user_id=user_id,
            title=title,
            original_filename=upload_file.filename or filename,
            original_path=saved_rel_path,
            status=VideoStatus.uploaded,
            file_size_mb=round(size_bytes / (1024 * 1024), 2),
            player_first_name=user_info.get("first_name", ""),
            player_last_name=user_info.get("last_name", ""),
            player_city=user_info.get("city", ""),
        )
        db.add(video)
        await db.flush()  # Flush para obtener ID sin commit

        input_path = saved_rel_path.replace("/uploads", settings.WORKER_INPUT_PREFIX, 1)
        correlation_id = f"req-{uuid.uuid4().hex[:12]}"

        # Actualizar correlation_id y status antes de encolar
        video.correlation_id = correlation_id
        video.status = VideoStatus.processing

        try:
            payload = {
                "video_id": str(video.id),
                "input_path": input_path,
                "correlation_id": correlation_id,
            }

            # Usar RabbitMQ con pool reutilizable
            pub = RabbitPublisher()
            try:
                pub.publish_video(payload)
            finally:
                pub.close()
            
            # Solo hacer commit si todo salió bien
            await db.commit()
        except Exception as e:
            # Si falla el encolado, revertir a uploaded para permitir reintento
            video.status = VideoStatus.uploaded
            video.correlation_id = None
            await db.rollback()
            raise HTTPException(status_code=502, detail=f"No se pudo encolar el procesamiento: {e}")

        return video, correlation_id

    def _validate_ext_and_size(self, file: UploadFile):
        _, ext = os.path.splitext(file.filename or "")
        ext = (ext or "").lower().lstrip(".")
        allowed = {x.lower() for x in settings.ALLOWED_VIDEO_FORMATS}
        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Formato no permitido. Usa: {', '.join(sorted(allowed)).upper()}.",
            )
        file.file.seek(0, os.SEEK_END)
        size_bytes = file.file.tell()
        file.file.seek(0)
        if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"El archivo supera {settings.MAX_UPLOAD_SIZE_MB} MB.",
            )
        return ext, size_bytes
