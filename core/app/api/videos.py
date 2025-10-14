"""
Router de gestión de videos
Endpoints para subir, listar, consultar y eliminar videos
"""

import select
from fastapi import APIRouter, status, HTTPException, UploadFile, File, Response, Form, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from uuid import UUID
import os, uuid

from pathlib import Path as SysPath
from app.config import settings                     # ⬅️ usar settings
from app.database import get_session                     # ⬅️ tu SessionLocal
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

router = APIRouter(prefix="/videos", tags=["Videos"])


# --- helpers ---
def _public_url_from_rel(rel_path: str | None) -> str | None:
    """
    Convierte una ruta relativa de storage (ej: '/uploads/2025/10/13/x.mp4')
    a una URL pública detrás de Nginx (ej: http://localhost:8080/media/uploads/...).
    """
    if not rel_path:
        return None
    # normaliza
    p = rel_path.replace("\\", "/")
    if p.startswith("/uploads"):
        suffix = p[len("/uploads"):]
        return f"{settings.PUBLIC_BASE_URL}{settings.PUBLIC_UPLOAD_PREFIX}{suffix}"
    if p.startswith("/processed"):
        suffix = p[len("/processed"):]
        return f"{settings.PUBLIC_BASE_URL}{settings.PUBLIC_PROCESSED_PREFIX}{suffix}"
    # fallback: asume uploads
    return f"{settings.PUBLIC_BASE_URL}{settings.PUBLIC_UPLOAD_PREFIX}{p}"

STORAGE_ROOT = "/app/storage"  # en el contenedor API (compose monta ./core/storage -> /app/storage)

def _abs_path_from_rel(rel_path: str) -> SysPath:
    """
    Asegura borrar sólo dentro de /app/storage (evita path traversal).
    """
    safe = rel_path.lstrip("/")
    return (SysPath(STORAGE_ROOT) / safe).resolve()

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
    db: AsyncSession = Depends(get_session),
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
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    # --- Guardar archivo ---
    storage = get_storage()
    filename = f"{uuid.uuid4().hex}.{ext}" if ext else (video_file.filename or uuid.uuid4().hex)
    saved_path = storage.save(video_file.file, filename, video_file.content_type or "application/octet-stream")

    # --- Crear registro en BD ---
    size_mb = round(size_bytes / (1024 * 1024), 2)

    # Mientras no haya auth, usa un user_id placeholder O haz la columna nullable=True:
    #placeholder_user_id = UUID("00000000-0000-0000-0000-000000000000")

    video = Video(
        #user_id=placeholder_user_id,  # <-- quita esto cuando tengas auth real
        title=title,
        original_filename=video_file.filename or filename,
        original_path=saved_path,     # guarda absoluta; si prefieres, guarda relativa a /app/storage
        status=VideoStatus.uploaded,
        file_size_mb=size_mb,
    )

    db.add(video)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        # por ejemplo, si user_id sigue NOT NULL y no lo pones, caerá aquí
        raise HTTPException(status_code=400, detail=f"Error guardando video en DB: {str(e.orig)}")

    await db.refresh(video)  # ahora video.id existe

    # --- correlation_id (usado como task_id de momento) ---
    correlation_id = f"req-{uuid.uuid4().hex[:12]}"

    # --- Path visto por el worker (si montas /app/storage/uploads -> /mnt/uploads) ---
    
    if settings.WORKER_INPUT_PREFIX:
        input_path = saved_path.replace("/uploads", settings.WORKER_INPUT_PREFIX, 1)
    else:
        input_path = f"/app/storage{saved_path}"

    # --- Publicar a Rabbit opcional (según env) ---
    if os.getenv("PUBLISH_TO_RABBIT", "false").lower() in {"1", "true", "yes"}:
        try:
            pub = RabbitPublisher()
            pub.publish_video({
                "video_id": str(video.id),
                "input_path": input_path,
                "correlation_id": correlation_id,
            })
            pub.close()
        except Exception:
            # marca como failed si no pudiste encolar (opcional)
            video.status = VideoStatus.failed
            db.add(video)
            await db.commit()
            raise HTTPException(status_code=502, detail="No se pudo encolar el procesamiento del video")

    # Header Location (opcional)
    response.headers["Location"] = f"/api/videos/{video.id}"

    return VideoUploadResponse(
        message="Video subido correctamente. Procesamiento en curso.",
        video_id=str(video.id),
        task_id=correlation_id,
    )                                                      

@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=List[VideoListItemResponse],
    summary="Listar videos",
    description="Lista videos disponibles. (Luego filtrar por usuario cuando haya auth)"
)
async def get_my_videos(
    db: AsyncSession = Depends(get_session),
    limit: int = 20,
    offset: int = 0,
) -> List[VideoListItemResponse]:
    stmt = (
        select(Video)
        .order_by(Video.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    videos = result.scalars().all()

    items: List[VideoListItemResponse] = []
    for v in videos:
        items.append(VideoListItemResponse(
            video_id=str(v.id),
            title=v.title,
            status=v.status.value if hasattr(v.status, "value") else v.status,
            uploaded_at=v.created_at,
            processed_at=v.processed_at,
            processed_url=_public_url_from_rel(v.processed_path) if v.status == VideoStatus.processed else None,
        ))
    return items


@router.get(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoResponse,
    summary="Consultar detalle de video",
    description="Detalle de un video (URLs públicas incluidas si existen)."
)
async def get_video_detail(
    video_id: str = Path(..., description="UUID del video"),
    db: AsyncSession = Depends(get_session),
) -> VideoResponse:
    try:
        _ = uuid.UUID(video_id)
    except Exception:
        raise HTTPException(status_code=400, detail="video_id no es un UUID válido")

    stmt = select(Video).where(Video.id == video_id)
    res = await db.execute(stmt)
    video: Video | None = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    # Conteo de votos (si tienes el modelo Vote; si no, deja 0)
    # votes_stmt = select(func.count()).select_from(Vote).where(Vote.video_id == video_id)
    # votes_res = await db.execute(votes_stmt)
    # votes_count = int(votes_res.scalar() or 0)
    votes_count = 0

    return VideoResponse(
        video_id=str(video.id),
        title=video.title,
        status=video.status.value if hasattr(video.status, "value") else video.status,
        uploaded_at=video.created_at,
        processed_at=video.processed_at,
        original_url=_public_url_from_rel(video.original_path),
        processed_url=_public_url_from_rel(video.processed_path) if video.processed_path else None,
        #votes=votes_count,
    )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoDeleteResponse,
    summary="Eliminar video",
    description="Elimina un video sólo si no está publicado (status != processed)."
)
async def delete_video(
    video_id: str = Path(..., description="UUID del video"),
    db: AsyncSession = Depends(get_session),
) -> VideoDeleteResponse:
    try:
        _ = uuid.UUID(video_id)
    except Exception:
        raise HTTPException(status_code=400, detail="video_id no es un UUID válido")

    res = await db.execute(select(Video).where(Video.id == video_id))
    video: Video | None = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    # (Cuando haya auth, valida que sea dueño aquí)

    if video.status == VideoStatus.processed:
        raise HTTPException(status_code=400, detail="El video ya está listo para votación; no puede eliminarse.")

    # Borrado de archivos en disco (si existen)
    try:
        if video.original_path:
            abs_orig = _abs_path_from_rel(video.original_path)
            if abs_orig.is_file():
                abs_orig.unlink(missing_ok=True)
        if video.processed_path:
            abs_proc = _abs_path_from_rel(video.processed_path)
            if abs_proc.is_file():
                abs_proc.unlink(missing_ok=True)
    except Exception:
        # No abortamos por fallo de IO; puedes loggear si deseas
        pass

    # Borrar en DB
    await db.delete(video)
    await db.commit()

    return VideoDeleteResponse(
        message="El video ha sido eliminado exitosamente.",
        video_id=video_id
    )
