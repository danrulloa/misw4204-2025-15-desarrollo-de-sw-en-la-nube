import logging
import os
import uuid
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.video import Video, VideoStatus
from app.services.storage._init_ import get_storage
from app.services.mq.rabbit import RabbitPublisher

import asyncio
import time
import inspect
from app.services.storage.executors import get_io_executor

logger = logging.getLogger("anb.uploads")


 


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
        correlation_id: str,
    ) -> Tuple[Video, str]:
        # Logs: entrada
        try:
            logger.info(
                "Entrando a LocalUploadService.upload",
                extra={
                    "correlation_id": correlation_id,
                    "usuario": user_id,
                    "titulo": title,
                    "archivo": getattr(upload_file, "filename", None),
                },
            )
        except Exception:
            pass

        # Start reception timer (monotonic)
        recv_start_perf = time.perf_counter()

        ext, size_bytes = self._validate_ext_and_size(upload_file, correlation_id=correlation_id)

        storage = get_storage()
        filename = f"{uuid.uuid4().hex}.{ext}"

        # STORAGE PHASE
        try:
            # Measure storage upload time
            storage_start_perf = time.perf_counter()

            # StoragePort.save es síncrono por contrato: ejecútalo en el pool I/O dedicado
            save_fn = getattr(storage, "save")
            loop = asyncio.get_running_loop()
            # Log entrada a almacenamiento
            try:
                logger.info(
                    "Guardando archivo en almacenamiento",
                    extra={"correlation_id": correlation_id, "filename": filename},
                )
            except Exception:
                pass
            saved_rel_path = await loop.run_in_executor(
                get_io_executor(),
                save_fn,
                upload_file.file,
                filename,
                upload_file.content_type or "application/octet-stream",
            )
            # Log salida de almacenamiento
            try:
                logger.info(
                    "Archivo guardado en almacenamiento",
                    extra={"correlation_id": correlation_id, "ruta": saved_rel_path},
                )
            except Exception:
                pass

            storage_end_perf = time.perf_counter()

            storage_duration_ms = (storage_end_perf - storage_start_perf) * 1000.0
            recv_duration_ms = (storage_start_perf - recv_start_perf) * 1000.0

            logger.info(
                "Upload phases timing",
                extra={
                    "user_id": user_id,
                    "filename": filename,
                    "reception_ms": round(recv_duration_ms, 3),
                    "storage_ms": round(storage_duration_ms, 3),
                },
            )

        except Exception as e:
            logger.exception(
                "Error guardando archivo en almacenamiento",
                extra={"correlation_id": correlation_id, "usuario": user_id, "titulo": title},
            )
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

        # Measure flush (part of DB persist)
        flush_start_perf = time.perf_counter()
        await db.flush()  # Flush para obtener ID sin commit
        flush_end_perf = time.perf_counter()
        flush_duration_ms = (flush_end_perf - flush_start_perf) * 1000.0

        # Generar input_path según el backend de almacenamiento
        if settings.STORAGE_BACKEND == "s3":
            # Para S3: generar ruta completa s3://bucket/key
            # saved_rel_path es como "/uploads/2025/11/02/uuid.mp4"
            # Necesitamos s3://bucket/uploads/2025/11/02/uuid.mp4
            s3_key = saved_rel_path.lstrip("/")  # "uploads/2025/11/02/uuid.mp4"
            input_path = f"s3://{settings.S3_BUCKET}/{s3_key}"
        else:
            # Local: mantener comportamiento actual
            input_path = saved_rel_path.replace("/uploads", settings.WORKER_INPUT_PREFIX, 1)
        
    # Actualizar correlation_id y status antes de encolar
        video.correlation_id = correlation_id
        video.status = VideoStatus.processing

        # MQ PHASE
        try:
            mq_start_perf = time.perf_counter()

            payload = {
                "video_id": str(video.id),
                "input_path": input_path,
                "correlation_id": correlation_id,
            }

            # Usar RabbitMQ con pool reutilizable
            pub = RabbitPublisher()
            try:
                pub_publish = getattr(pub, "publish_video")
                if inspect.iscoroutinefunction(pub_publish):
                    await pub_publish(payload)
                else:
                    # Ejecutar la publicación en un hilo para no bloquear el event loop
                    await asyncio.to_thread(pub_publish, payload)
            finally:
                # Cerrar el cliente/pool; soportar close async o sync
                pub_close = getattr(pub, "close", None)
                if pub_close:
                    if inspect.iscoroutinefunction(pub_close):
                        await pub_close()
                    else:
                        try:
                            await asyncio.to_thread(pub_close)
                        except Exception:
                            # No queremos que el cierre falle la ruta principal
                            pass

            mq_end_perf = time.perf_counter()
            mq_duration_ms = (mq_end_perf - mq_start_perf) * 1000.0

            logger.info(
                "Publicación en MQ completada",
                extra={
                    "video_id": str(video.id),
                    "correlation_id": correlation_id,
                    "duracion_mq_ms": round(mq_duration_ms, 3),
                },
            )

            # DB commit (persist) - measure commit duration
            db_commit_start_perf = time.perf_counter()
            await db.commit()
            db_commit_end_perf = time.perf_counter()
            db_commit_duration_ms = (db_commit_end_perf - db_commit_start_perf) * 1000.0

            total_db_ms = round(flush_duration_ms + db_commit_duration_ms, 3)
            logger.info(
                "Transacción en BD completada",
                extra={
                    "video_id": str(video.id),
                    "correlation_id": correlation_id,
                    "db_flush_ms": round(flush_duration_ms, 3),
                    "db_commit_ms": round(db_commit_duration_ms, 3),
                    "db_total_ms": total_db_ms,
                },
            )

        except Exception as e:
            # Si falla el encolado, revertir a uploaded para permitir reintento
            video.status = VideoStatus.uploaded
            video.correlation_id = None
            await db.rollback()
            logger.exception(
                "Error encolando mensaje en MQ",
                extra={"video_id": str(video.id), "correlation_id": correlation_id},
            )
            raise HTTPException(status_code=502, detail=f"No se pudo encolar el procesamiento: {e}")

        logger.info(
            "Saliendo de LocalUploadService.upload",
            extra={"video_id": str(video.id), "correlation_id": correlation_id, "usuario": user_id},
        )
        return video, correlation_id

    def _validate_ext_and_size(self, file: UploadFile, *, correlation_id: str | None = None):
        try:
            logger.info(
                "Entrando a validación de extensión y tamaño",
                extra={"correlation_id": correlation_id, "archivo": getattr(file, "filename", None)},
            )
        except Exception:
            pass
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
        try:
            logger.info(
                "Saliendo de validación de extensión y tamaño",
                extra={"correlation_id": correlation_id, "tamano_bytes": size_bytes, "extension": ext},
            )
        except Exception:
            pass
        return ext, size_bytes