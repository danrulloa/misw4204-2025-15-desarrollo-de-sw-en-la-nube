"""
Router de gestión de videos
Endpoints para subir, listar, consultar y eliminar videos
"""

from fastapi import APIRouter, status, HTTPException, UploadFile, File, Form, Response, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os, uuid, jwt
from pathlib import Path as PathLib
from app.config import settings
from app.database import get_session
from app.models.video import Video, VideoStatus
from app.services.storage._init_ import get_storage
from app.services.mq.rabbit import RabbitPublisher
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from app.schemas.video import (
    VideoUploadResponse,
    VideoListItemResponse,
    VideoResponse,
    VideoDeleteResponse
)

router = APIRouter(prefix="/videos", tags=["Videos"])
_bearer = HTTPBearer(auto_error=True)

def _current_user_id(creds: HTTPAuthorizationCredentials) -> str:
    try:
        payload = jwt.decode(
             creds.credentials,
             os.getenv("ACCESS_TOKEN_SECRET_KEY", ""),
             algorithms=[os.getenv("ALGORITHM", "HS256")],
             options={"require": ["exp", "iat"], "verify_aud": False, "verify_iss": False},
             audience=os.getenv("AUTH_AUDIENCE", "anb-api"),
             issuer=os.getenv("AUTH_ISSUER", "anb-auth"),
        )
        sub = payload.get("sub")
        if not sub:
                raise ValueError("El token no trae 'sub'")
        return str(sub)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")
    
def _validate_ext_and_size(file: UploadFile):
    _, ext = os.path.splitext(file.filename or "")
    ext = (ext or "").lower().lstrip(".")
    allowed = {x.lower() for x in settings.ALLOWED_VIDEO_FORMATS}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Formato no permitido. Usa: {', '.join(sorted(allowed)).upper()}.")
    file.file.seek(0, os.SEEK_END)
    size_bytes = file.file.tell()
    file.file.seek(0)
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"El archivo supera {settings.MAX_UPLOAD_SIZE_MB} MB.")
    return ext, size_bytes

def _abs_storage_path(rel_path: str) -> PathLib:
    """Convierte rutas relativas de BD a rutas absolutas del contenedor"""
    if not rel_path:
        return PathLib("/non/existent")
    if rel_path.startswith("/uploads"):
        return PathLib(rel_path.replace("/uploads", settings.UPLOAD_DIR, 1))
    if rel_path.startswith("/processed"):
        return PathLib(rel_path.replace("/processed", settings.PROCESSED_DIR, 1))
    return PathLib(settings.UPLOAD_DIR.rstrip("/")) / rel_path.lstrip("/")

def _get_user_from_request(request: Request) -> dict:
    """Extrae información del usuario desde request.state"""
    user = request.state.user
    return {
        "user_id": user.get("user_id"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "city": user.get("city", "")
    }

@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=VideoUploadResponse,
    summary="Subir video"
)
async def upload_video(
    request: Request,
    response: Response,
    video_file: UploadFile = File(..., description="Archivo de video"),
    title: str = Form(..., description="Título del video"),
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> VideoUploadResponse:

    user_id = _current_user_id(creds)
    ext, size_bytes = _validate_ext_and_size(video_file)

    storage = get_storage()
    filename = f"{uuid.uuid4().hex}.{ext}"
    saved_rel_path = storage.save(video_file.file, filename, video_file.content_type or "application/octet-stream")

    user_info = _get_user_from_request(request)

    video = Video(
        user_id=user_id,
        title=title,
        original_filename=video_file.filename or filename,
        original_path=saved_rel_path,
        status=VideoStatus.uploaded,
        file_size_mb=round(size_bytes / (1024*1024), 2),
        player_first_name=user_info["first_name"],
        player_last_name=user_info["last_name"],
        player_city=user_info["city"]
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    input_path = saved_rel_path.replace("/uploads", settings.WORKER_INPUT_PREFIX, 1)
    correlation_id = f"req-{uuid.uuid4().hex[:12]}"
    
    # Persistir correlation_id y marcar en procesamiento antes de encolar
    video.correlation_id = correlation_id
    video.status = VideoStatus.processing
    await db.commit()
    await db.refresh(video)

    try:
        payload = {
            "video_id": str(video.id),
            "input_path": input_path,
            "correlation_id": correlation_id,
        }

        pub = RabbitPublisher()
        try:
            pub.publish_video(payload)
        finally:
            pub.close()
    except Exception as e:
        # Si falla el encolado, revertir a uploaded para permitir reintento
        video.status = VideoStatus.uploaded
        video.correlation_id = None
        await db.commit()
        raise HTTPException(status_code=502, detail=f"No se pudo encolar el procesamiento: {e}")

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
    summary="Listar mis videos",
    description="Obtiene la lista de videos del usuario autenticado",
)
async def get_my_videos(
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    limit: int = 20,
    offset: int = 0,
) -> List[VideoListItemResponse]:
    user_id = _current_user_id(creds)

    stmt = (
        select(Video)
        .where(Video.user_id == user_id)
        .order_by(Video.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)
    videos = res.scalars().all()

    return [
        VideoListItemResponse(
            video_id=str(v.id),
            title=v.title,
            status=v.status,
            uploaded_at=v.created_at,
            processed_at=v.processed_at,
            processed_url=None,
        )
        for v in videos
    ]


@router.get(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoResponse,
    summary="Consultar detalle de video",
    description="Detalle de un video del usuario autenticado",
)
async def get_video_detail(
    video_id: str = Path(..., description="UUID del video"),
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> VideoResponse:
    user_id = _current_user_id(creds)

    res = await db.execute(select(Video).where(Video.id == video_id))
    video: Video | None = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    if str(video.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="El video no pertenece al usuario")

    votes_count = 0

    return VideoResponse(
        video_id=str(video.id),
        title=video.title,
        status=video.status,
        uploaded_at=video.created_at,
        processed_at=video.processed_at,
        original_url=None,
        processed_url=None,
        votes=votes_count,
    )


@router.delete(
    "/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=VideoDeleteResponse,
    summary="Eliminar video",
    description="Elimina un video propio si aún no está publicado (status != processed).",
)
async def delete_video(
    video_id: str,
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> VideoDeleteResponse:
    user_id = _current_user_id(creds)

    res = await db.execute(select(Video).where(Video.id == video_id))
    video: Video | None = res.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    if str(video.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="El video no pertenece al usuario")

    if video.status == VideoStatus.processed:
        raise HTTPException(
            status_code=400,
            detail="El video ya está listo para votación; no puede eliminarse."
        )

    try:
        if video.original_path:
            p = _abs_storage_path(video.original_path)
            if p.is_file():
                p.unlink(missing_ok=True)
        if video.processed_path:
            p = _abs_storage_path(video.processed_path)
            if p.is_file():
                p.unlink(missing_ok=True)
    except Exception:
        pass

    await db.delete(video)
    await db.commit()

    return VideoDeleteResponse(
        message="El video ha sido eliminado exitosamente.",
        video_id=str(video_id),
    )
