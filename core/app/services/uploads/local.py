import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Tuple
import time

from fastapi import HTTPException, UploadFile, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.video import Video, VideoStatus
from app.services.storage.s3 import S3StorageAdapter
from app.services.mq.rabbit import RabbitPublisher

logger = logging.getLogger("anb.uploads")


class _LazyS3Storage:
    """Instancia perezosa de S3 para evitar inicializar en import.

    Se crea el adapter real en el primer uso (save). Siempre usa S3.
    """

    def __init__(self) -> None:
        self._adapter: S3StorageAdapter | None = None

    def _ensure(self) -> S3StorageAdapter:
        if self._adapter is None:
            self._adapter = S3StorageAdapter(
                bucket=settings.S3_BUCKET,
                prefix=settings.S3_PREFIX,
                region=settings.S3_REGION,
                endpoint_url=settings.S3_ENDPOINT_URL or None,
                force_path_style=settings.S3_FORCE_PATH_STYLE,
                verify_ssl=settings.S3_VERIFY_SSL,
                access_key_id=settings.AWS_ACCESS_KEY_ID,
                secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                session_token=settings.AWS_SESSION_TOKEN,
            )
        return self._adapter

    # Cumple el contrato de StoragePort
    def save(self, fileobj, filename, content_type) -> str:  # type: ignore[override]
        return self._ensure().save(fileobj, filename, content_type)

    def save_with_key(self, fileobj, key: str, content_type) -> str:  # type: ignore[override]
        return self._ensure().save_with_key(fileobj, key, content_type)


# S3 como backend fijo (perezoso para no fallar al importar si faltan vars)
STORAGE = _LazyS3Storage()


class LocalUploadService:
    """Implementación del servicio de subida de videos con S3-only y pipeline en background."""

    async def upload(
        self,
        *,
        user_id: str,
        title: str,
        upload_file: UploadFile,
        user_info: Dict[str, str],
        db: AsyncSession,
        correlation_id: str,
        background_tasks: BackgroundTasks | None = None,
    ) -> Tuple[Video, str]:
        """Valida, persiste el Video y programa el pipeline en background.

        Retorna el Video y el correlation_id inmediatamente, sin subir el archivo en el request.
        """
        # Log de entrada y cronómetro del camino crítico del request
        req_t0 = time.perf_counter()
        logger.info(
            "upload:start corr=%s user=%s title=%s",
            correlation_id,
            user_id,
            title,
        )

        ext, size_bytes = self._validate_ext_and_size(upload_file, correlation_id=correlation_id)
        logger.info(
            "upload:validated corr=%s ext=%s size_bytes=%s",
            correlation_id,
            ext,
            size_bytes,
        )

        # Precomputar key S3 para responder sin esperar el upload
        today = datetime.utcnow()
        day_dir = f"{today:%Y}/{today:%m}/{today:%d}"
        basename = f"{uuid.uuid4().hex}.{ext}"
        s3_key = f"{settings.S3_PREFIX.strip('/')}/{day_dir}/{uuid.uuid4().hex}-{basename}"
        saved_rel_path = f"/{s3_key}"  # ruta lógica

        # Persistir Video (commit temprano)
        video = Video(
            user_id=user_id,
            title=title,
            original_filename=upload_file.filename or basename,
            original_path=saved_rel_path,
            status=VideoStatus.uploaded,
            file_size_mb=round(size_bytes / (1024 * 1024), 2),
            player_first_name=user_info.get("first_name", ""),
            player_last_name=user_info.get("last_name", ""),
            player_city=user_info.get("city", ""),
            correlation_id=correlation_id,
        )
        logger.info("upload:db:persist corr=%s", correlation_id)
        db.add(video)
        await db.flush()
        await db.commit()  # commit temprano; estado uploaded
        req_ms = (time.perf_counter() - req_t0) * 1000.0
        logger.info(
            "upload:db:committed corr=%s video_id=%s elapsed_ms=%.1f",
            correlation_id,
            video.id,
            req_ms,
        )

        input_path = f"s3://{settings.S3_BUCKET}/{s3_key}"  # pasado al worker

        # Programar procesamiento en background (obligatorio)
        if background_tasks is None:
            logger.error(
                "BackgroundTasks no disponible; no se puede ejecutar pipeline asíncrono corr=%s",
                correlation_id,
            )
            raise HTTPException(status_code=500, detail="Background processing no disponible")

        background_tasks.add_task(
            self._background_pipeline,
            upload_file,
            s3_key,
            str(video.id),
            input_path,
            correlation_id,
            upload_file.content_type or "application/octet-stream",
        )
        logger.info(
            "upload:bg:scheduled corr=%s video_id=%s key=%s input=%s",
            correlation_id,
            video.id,
            s3_key,
            input_path,
        )
        return video, correlation_id

    def _validate_ext_and_size(self, file: UploadFile, *, correlation_id: str | None = None):

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

    def _background_pipeline(
        self,
        upload_file: UploadFile,
        s3_key: str,
        video_id: str,
        input_path: str,
        correlation_id: str,
        content_type: str,
    ) -> None:
        """Pipeline ejecutada después de enviar la respuesta (no async-await)."""
        try:
            bg_t0 = time.perf_counter()
            logger.info(
                "bg:start corr=%s video_id=%s key=%s",
                correlation_id,
                video_id,
                s3_key,
            )
            # Subir a S3
            s3_t0 = time.perf_counter()
            STORAGE.save_with_key(upload_file.file, s3_key, content_type)
            s3_ms = (time.perf_counter() - s3_t0) * 1000.0
            logger.info(
                "bg:s3:uploaded corr=%s key=%s elapsed_ms=%.1f",
                correlation_id,
                s3_key,
                s3_ms,
            )
            # Publicar en MQ
            mq_t0 = time.perf_counter()
            pub = RabbitPublisher()
            payload = {
                "video_id": video_id,
                "input_path": input_path,
                "correlation_id": correlation_id,
            }
            try:
                pub.publish_video(payload)
            finally:
                close_fn = getattr(pub, "close", None)
                if close_fn:
                    try:
                        close_fn()
                    except Exception:
                        pass
            mq_ms = (time.perf_counter() - mq_t0) * 1000.0
            total_ms = (time.perf_counter() - bg_t0) * 1000.0
            logger.info(
                "bg:done corr=%s video_id=%s s3_ms=%.1f mq_ms=%.1f total_ms=%.1f",
                correlation_id,
                video_id,
                s3_ms,
                mq_ms,
                total_ms,
            )
        except Exception as e:
            logger.exception("bg:error corr=%s err=%s", correlation_id, e)
