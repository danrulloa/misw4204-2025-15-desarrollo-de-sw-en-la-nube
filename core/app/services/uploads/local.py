import asyncio
import inspect
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models.video import Video, VideoStatus
from app.services.mq.rabbit import RabbitPublisher
from app.services.storage._init_ import get_storage
from app.services.storage.executors import get_io_executor

logger = logging.getLogger("anb.uploads")


class LocalUploadService:
    """Implementacion local del servicio de subida de videos."""

    def __init__(self, *, process_inline: bool | None = None, staging_root: Path | None = None) -> None:
        self._process_inline = (
            process_inline
            if process_inline is not None
            else getattr(settings, "UPLOAD_SYNC_PIPELINE", False)
        )
        root = staging_root
        if root is None:
            env_path = getattr(settings, "UPLOAD_STAGING_DIR", None)
            if env_path:
                root = Path(env_path)
            else:
                import tempfile

                root = Path(tempfile.gettempdir()) / "anb_staging"
        self._staging_root = root
        try:
            self._staging_root.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.warning("No se pudo crear staging dir %s", self._staging_root, exc_info=True)

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
        filename = f"{uuid.uuid4().hex}.{ext}"

        staging_path = await self._stage_upload_file(upload_file, filename)  # REF1
        placeholder_rel_path = f"/staging/{staging_path.name}"

        video, correlation_id, flush_duration_ms = await self._create_video_record(  # REF2
            db=db,
            user_id=user_id,
            title=title,
            upload_file=upload_file,
            filename=filename,
            saved_rel_path=placeholder_rel_path,
            size_bytes=size_bytes,
            user_info=user_info,
        )

        await db.commit()  # Commit temprano para que la tarea de fondo vea el registro

        logger.info(
            "Upload accepted, encolando procesamiento async",
            extra={"video_id": str(video.id), "correlation_id": correlation_id, "user_id": user_id},
        )

        pipeline_kwargs = dict(
            video_id=video.id,
            correlation_id=correlation_id,
            staging_path=staging_path,
            filename=filename,
            content_type=upload_file.content_type or "application/octet-stream",
            flush_duration_ms=flush_duration_ms,
        )
        if self._process_inline:
            await self._process_pipeline(**pipeline_kwargs)
        else:
            self._schedule_background_pipeline(**pipeline_kwargs)  # REF3

        return video, correlation_id

    async def _create_video_record(
        self,
        *,
        db: AsyncSession,
        user_id: str,
        title: str,
        upload_file: UploadFile,
        filename: str,
        saved_rel_path: str,
        size_bytes: int,
        user_info: Dict[str, str],
    ) -> Tuple[Video, str, float]:
        """REF2: registra el video y calcula metadata previa al procesamiento."""
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

        flush_start_perf = time.perf_counter()
        await db.flush()
        flush_end_perf = time.perf_counter()
        flush_duration_ms = (flush_end_perf - flush_start_perf) * 1000.0

        correlation_id = f"req-{uuid.uuid4().hex[:12]}"
        video.correlation_id = correlation_id
        video.status = VideoStatus.uploaded

        return video, correlation_id, flush_duration_ms

    def _schedule_background_pipeline(
        self,
        *,
        video_id,
        correlation_id: str,
        staging_path: Path,
        filename: str,
        content_type: str,
        flush_duration_ms: float,
    ) -> None:
        """REF3: lanza una corrutina que har� el upload real + MQ."""
        async def runner() -> None:
            await self._process_pipeline(
                video_id=video_id,
                correlation_id=correlation_id,
                staging_path=staging_path,
                filename=filename,
                content_type=content_type,
                flush_duration_ms=flush_duration_ms,
            )

        task = asyncio.create_task(runner())
        task.add_done_callback(lambda t: self._log_task_result(t, video_id))

    async def _enqueue_processing(
        self,
        *,
        video: Video,
        input_path: str,
        correlation_id: str,
        flush_duration_ms: float,
        db: AsyncSession,
    ) -> None:
        """REF3: publica en RabbitMQ y finaliza la transaccion."""
        try:
            mq_start_perf = time.perf_counter()
            payload = {
                "video_id": str(video.id),
                "input_path": input_path,
                "correlation_id": correlation_id,
            }

            pub = RabbitPublisher()
            try:
                pub_publish = getattr(pub, "publish_video")
                if inspect.iscoroutinefunction(pub_publish):
                    await pub_publish(payload)
                else:
                    await asyncio.to_thread(pub_publish, payload)
            finally:
                pub_close = getattr(pub, "close", None)
                if pub_close:
                    if inspect.iscoroutinefunction(pub_close):
                        await pub_close()
                    else:
                        try:
                            await asyncio.to_thread(pub_close)
                        except Exception:
                            pass

            mq_end_perf = time.perf_counter()
            mq_duration_ms = (mq_end_perf - mq_start_perf) * 1000.0
            logger.info(
                "MQ publish timing",
                extra={
                    "video_id": str(video.id),
                    "correlation_id": correlation_id,
                    "mq_ms": round(mq_duration_ms, 3),
                },
            )

            db_commit_start_perf = time.perf_counter()
            await db.commit()
            db_commit_end_perf = time.perf_counter()
            db_commit_duration_ms = (db_commit_end_perf - db_commit_start_perf) * 1000.0

            total_db_ms = round(flush_duration_ms + db_commit_duration_ms, 3)
            logger.info(
                "DB timing",
                extra={
                    "video_id": str(video.id),
                    "db_flush_ms": round(flush_duration_ms, 3),
                    "db_commit_ms": round(db_commit_duration_ms, 3),
                    "db_total_ms": total_db_ms,
                },
            )
        except Exception as e:
            video.status = VideoStatus.uploaded
            video.correlation_id = None
            await db.rollback()
            logger.exception(
                "Upload failed enqueuing message",
                extra={"video_id": str(video.id), "correlation_id": correlation_id},
            )
            raise HTTPException(status_code=502, detail=f"No se pudo encolar el procesamiento: {e}")

    def _log_task_result(self, task: asyncio.Task, video_id) -> None:
        try:
            task.result()
        except Exception:
            logger.exception("Tarea de upload async fall� para video %s", video_id)

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

    async def _process_pipeline(
        self,
        *,
        video_id,
        correlation_id: str,
        staging_path: Path,
        filename: str,
        content_type: str,
        flush_duration_ms: float,
    ) -> None:
        """Carga el archivo staged a storage y encola el procesamiento."""
        try:
            storage = get_storage()
            try:
                saved_rel_path = await self._upload_staged_file(
                    storage=storage,
                    staging_path=staging_path,
                    filename=filename,
                    content_type=content_type,
                )
            except Exception:
                await self._mark_failed(video_id, reason="upload_failed")
                raise

            if settings.STORAGE_BACKEND == "s3":
                s3_key = saved_rel_path.lstrip("/")
                input_path = f"s3://{settings.S3_BUCKET}/{s3_key}"
            else:
                input_path = saved_rel_path.replace("/uploads", settings.WORKER_INPUT_PREFIX, 1)

            async with SessionLocal() as session:
                video = await session.get(Video, video_id)
                if not video:
                    logger.error("Video %s no encontrado para encolar", video_id)
                    return

                video.original_path = saved_rel_path
                video.status = VideoStatus.processing

                await self._enqueue_processing(
                    video=video,
                    input_path=input_path,
                    correlation_id=correlation_id,
                    flush_duration_ms=flush_duration_ms,
                    db=session,
                )
        finally:
            try:
                staging_path.unlink(missing_ok=True)
            except Exception:
                logger.warning("No se pudo borrar staging %s", staging_path)

    async def _upload_staged_file(
        self,
        *,
        storage,
        staging_path: Path,
        filename: str,
        content_type: str,
    ) -> str:
        """Sube el archivo staged reutilizando el mismo adapter sync."""
        loop = asyncio.get_running_loop()
        save_fn = getattr(storage, "save")

        def _upload() -> str:
            with open(staging_path, "rb") as fh:
                return save_fn(fh, filename, content_type)

        return await loop.run_in_executor(get_io_executor(), _upload)

    async def _mark_failed(self, video_id, reason: str) -> None:
        async with SessionLocal() as session:
            video = await session.get(Video, video_id)
            if not video:
                return
            video.status = VideoStatus.failed
            video.correlation_id = None
            await session.commit()
            logger.error("Video %s marcado como failed (%s)", video_id, reason)

    async def _stage_upload_file(self, upload_file: UploadFile, filename: str) -> Path:
        """REF1: mueve/copia el archivo recibido a un staging local r�pido."""
        staging_path = self._staging_root / f"{uuid.uuid4().hex}-{filename}"
        loop = asyncio.get_running_loop()

        source_path = getattr(upload_file.file, "name", None)
        upload_file.file.seek(0)

        if source_path and os.path.exists(source_path):
            await loop.run_in_executor(None, shutil.copy2, source_path, staging_path)
        else:
            await loop.run_in_executor(None, self._copy_stream, upload_file.file, staging_path)

        upload_file.file.seek(0)
        return staging_path

    def _copy_stream(self, fileobj, dest_path: Path) -> None:
        fileobj.seek(0)
        with open(dest_path, "wb") as dst:
            shutil.copyfileobj(fileobj, dst)
