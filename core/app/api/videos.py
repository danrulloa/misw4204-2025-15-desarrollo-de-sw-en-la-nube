"""
Router de gestión de videos
Endpoints para subir, listar, consultar y eliminar videos
"""

from fastapi import APIRouter, status, HTTPException, UploadFile, File, Response, Form, Depends
from sqlalchemy.orm import Session
import os, uuid

from app.config import settings                     # ⬅️ usar settings
from app.database import get_db                     # ⬅️ tu SessionLocal
from app.models.video import Video, VideoStatus     # ⬅️ modelo real
from app.services.mq.rabbit import RabbitPublisher  # ⬅️ publisher a Rabbit
from typing import List
from app.schemas.video import (
    VideoUploadResponse,
    VideoListItemResponse,
    VideoResponse,
    VideoDeleteResponse
)
from app.schemas.common import ErrorResponse
from app.config import ALLOWED_VIDEO_FORMATS, MAX_UPLOAD_SIZE_MB
from app.services.storage import get_storage

router = APIRouter(prefix="/api/videos", tags=["Videos"])

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=VideoUploadResponse,
    summary="Subir video",
    description="Permite a un jugador subir un video demostrando sus habilidades",
)
async def upload_video(
    response: Response,
    video_file: UploadFile = File(..., description="Archivo de video (MP4, máximo 100MB)"),
    title: str = Form(..., description="Título descriptivo del video"),
    db: Session = Depends(get_db),                       # ⬅️ inyecta sesión
) -> VideoUploadResponse:
    # --- Validación extensión ---
    _, ext = os.path.splitext(video_file.filename or "")
    ext = (ext or "").lower().lstrip(".")
    allowed = {x.lower() for x in settings.ALLOWED_VIDEO_FORMATS}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Formato no permitido. Usa: {', '.join(sorted(allowed)).upper()}.")

    # --- Validación tamaño ---
    video_file.file.seek(0, os.SEEK_END)
    size_bytes = video_file.file.tell()
    video_file.file.seek(0)
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"El archivo supera {settings.MAX_UPLOAD_SIZE_MB} MB.")

    # --- Guardar archivo (contrato de storage) ---
    storage = get_storage()
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else (video_file.filename or uuid.uuid4().hex)
    saved_path = storage.save(video_file.file, filename, video_file.content_type or "application/octet-stream")

    # --- Crear registro en BD y obtener video_id real ---
    size_mb = round(size_bytes / (1024 * 1024), 2)
    video = Video(
        title=title,
        original_filename=video_file.filename or filename,
        original_path=saved_path,               # ruta que guardaste
        status=VideoStatus.uploaded,
        file_size_mb=size_mb,
        # user_id= current_user.id  # cuando exista auth
    )
    db.add(video)
    db.commit()
    db.refresh(video)                           # ⬅️ ahora video.id está disponible

    # --- correlation_id (lo usamos como task_id por ahora) ---
    correlation_id = f"req-{uuid.uuid4().hex[:12]}"

    # --- Path que verá el worker (si montas el volumen en /mnt/uploads) ---
    worker_prefix = os.getenv("WORKER_INPUT_PREFIX")  # ej: /mnt/uploads
    if worker_prefix:
        # mapear .../storage/uploads/... -> /mnt/uploads/...
        norm = saved_path.replace("\\", "/")
        parts = norm.split("/storage/uploads", 1)
        input_path = worker_prefix + (parts[1] if len(parts) > 1 else "")
    else:
        input_path = saved_path

    # --- Publicar mensaje a RabbitMQ (exchange 'video') ---
    try:
        pub = RabbitPublisher()
        pub.publish_video({
            "video_id": str(video.id),        # lo que el worker usará para actualizar BD
            "input_path": input_path,
            "correlation_id": correlation_id,
        })
        pub.close()
    except Exception:
        # si el publish falla, marca el video como failed
        video.status = VideoStatus.failed
        db.add(video); db.commit()
        raise HTTPException(status_code=502, detail="No se pudo encolar el procesamiento del video")

    # Header Location (opcional)
    response.headers["Location"] = f"/api/videos/{video.id}"

    return VideoUploadResponse(
        message="Video subido correctamente. Procesamiento en curso.",
        video_id=str(video.id),          # ⬅️ id real de BD
        task_id=correlation_id,          # ⬅️ usamos correlation como task_id
    )

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[VideoListItemResponse],
    summary="Listar mis videos",
    description="Obtiene la lista de videos subidos por el usuario autenticado",
    responses={
        200: {
            "description": "Lista de videos obtenida",
            "model": List[VideoListItemResponse]
        },
        401: {
            "description": "Falta de autenticación",
            "model": ErrorResponse
        }
    }
)
async def get_my_videos() -> List[VideoListItemResponse]:
    """
    Lista todos los videos del usuario autenticado.
    
    Muestra el estado de cada video:
    - uploaded: Recién subido
    - processing: En proceso
    - processed: Listo para visualización
    - failed: Error en procesamiento
    """
    # TODO: Implementar cuando se tenga DB y auth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )


@router.get(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoResponse,
    summary="Consultar detalle de video",
    description="Obtiene el detalle completo de un video específico del usuario",
    responses={
        200: {
            "description": "Detalle del video obtenido",
            "model": VideoResponse
        },
        401: {
            "description": "Falta de autenticación",
            "model": ErrorResponse
        },
        403: {
            "description": "El video no pertenece al usuario",
            "model": ErrorResponse
        },
        404: {
            "description": "Video no encontrado",
            "model": ErrorResponse
        }
    }
)
async def get_video_detail(video_id: str) -> VideoResponse:
    """
    Obtiene el detalle completo de un video.
    
    Incluye:
    - Información básica
    - Estado de procesamiento
    - URLs de descarga (si está procesado)
    - Número de votos
    """
    # TODO: Implementar cuando se tenga DB y auth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoDeleteResponse,
    summary="Eliminar video",
    description="Elimina un video propio, solo si no ha sido publicado para votación",
    responses={
        200: {
            "description": "Video eliminado exitosamente",
            "model": VideoDeleteResponse
        },
        400: {
            "description": "El video no puede ser eliminado (ya está en votación)",
            "model": ErrorResponse
        },
        401: {
            "description": "Falta de autenticación",
            "model": ErrorResponse
        },
        403: {
            "description": "El video no pertenece al usuario",
            "model": ErrorResponse
        },
        404: {
            "description": "Video no encontrado",
            "model": ErrorResponse
        }
    }
)
async def delete_video(video_id: str) -> VideoDeleteResponse:
    """
    Elimina un video del usuario.
    
    Restricciones:
    - Solo se pueden eliminar videos propios
    - No se pueden eliminar videos ya publicados para votación
    - Se eliminan tanto el archivo original como el procesado
    """
    # TODO: Implementar cuando se tenga DB, auth y storage
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB y storage."
    )
