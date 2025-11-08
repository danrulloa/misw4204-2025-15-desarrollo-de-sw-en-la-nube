import logging
import os
import uuid
from typing import Dict, Tuple

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.video import Video, VideoStatus
from app.services.storage.s3 import S3StorageAdapter
from app.services.mq.rabbit import RabbitPublisher

import asyncio
import time
import inspect
from app.services.storage.executors import get_io_executor

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


# S3 como backend fijo (perezoso para no fallar al importar si faltan vars)
STORAGE = _LazyS3Storage()


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
        # Log de entrada
        logger.info("Entrando a LocalUploadService.upload %s", correlation_id)

        ext, size_bytes = self._validate_ext_and_size(upload_file, correlation_id=correlation_id)

        logger.info("Usando almacenamiento S3 preconfigurado %s", correlation_id)
        storage = STORAGE

        logger.info("Obtenido el storage %s", correlation_id)
        filename = f"{uuid.uuid4().hex}.{ext}"

        # STORAGE PHASE
        try:

            logger.info("Llama al get attribute con: %s", correlation_id)
            # StoragePort.save es síncrono por contrato: ejecútalo en el pool I/O dedicado
            save_fn = getattr(storage, "save")

            logger.info("Obtiene al get attribute con: %s", correlation_id)

            logger.info("Llama al loop con: %s", correlation_id)
            loop = asyncio.get_running_loop()

            logger.info("Llamó al loop con: %s", correlation_id)
            
            logger.info("Guardando archivo en almacenamiento %s", correlation_id)

         
            saved_rel_path = await loop.run_in_executor(
                get_io_executor(),
                save_fn,
                upload_file.file,
                filename,
                upload_file.content_type or "application/octet-stream",
            )

            logger.info("Completa el guardado del archivo en almacenamiento %s", correlation_id)

        except Exception as e:
            logger.info("Error el guardado del archivo en almacenamiento %s %s", correlation_id, e)
            raise HTTPException(status_code=502, detail=f"Error guardando archivo en storage: {e}")

        logger.info("Empieza la creación del objeto Video %s", correlation_id)
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
            correlation_id=correlation_id
        )
        logger.info("empieza a guardar en DB %s", correlation_id)
        db.add(video)

  
        await db.flush()  # Flush para obtener ID sin commit
        
        logger.info("termina a guardar en DB con flush %s", correlation_id)


        logger.info("Construyendo key S3 de almacenamiento %s", correlation_id)
        # Siempre S3: generar ruta completa s3://bucket/key
        # saved_rel_path es como "/uploads/2025/11/02/uuid.mp4"
        # Necesitamos s3://bucket/uploads/2025/11/02/uuid.mp4
        s3_key = saved_rel_path.lstrip("/")  # "uploads/2025/11/02/uuid.mp4"
        input_path = f"s3://{settings.S3_BUCKET}/{s3_key}"

        logger.info("Termina el key de almacenamiento %s", correlation_id)

    
        video.status = VideoStatus.processing

        logger.info("empieza a enviar en MQ %s", correlation_id)
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

            logger.info("Publicación en MQ completada %s", correlation_id)
            await db.commit()
            logger.info("Commit en DB completado %s", correlation_id)


        except Exception as e:
            # Si falla el encolado, revertir a uploaded para permitir reintento
            video.status = VideoStatus.uploaded
            video.correlation_id = None
            await db.rollback()
            logger.exception("Error encolando mensaje en MQ %s %s", correlation_id, e)
            raise HTTPException(status_code=502, detail=f"No se pudo encolar el procesamiento: {e}")

        logger.info("Saliendo de LocalUploadService.upload %s", correlation_id)
        return video, correlation_id

    def _validate_ext_and_size(self, file: UploadFile, *, correlation_id: str | None = None):

        logger.info("Entrando a LocalUploadService.upload %s", correlation_id)

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
        logger.info("Saliendo de la validación de extensión y tamaño %s", correlation_id)
        return ext, size_bytes