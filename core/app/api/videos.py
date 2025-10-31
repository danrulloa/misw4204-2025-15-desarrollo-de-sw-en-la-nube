"""
Router de gestión de videos
Endpoints para subir, listar, consultar y eliminar videos
"""

from fastapi import APIRouter, status, HTTPException, UploadFile, File, Form, Response, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os, jwt
from app.database import get_session
from app.models.video import Video, VideoStatus
from app.services.uploads._init_ import get_upload_service
from app.services.uploads.base import UploadServicePort
from app.services.storage.utils import abs_storage_path
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
    user_info = _get_user_from_request(request)

    service: UploadServicePort = get_upload_service()
    video, correlation_id = await service.upload(
        user_id=user_id,
        title=title,
        upload_file=video_file,
        user_info=user_info,
        db=db,
    )

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

    return VideoDeleteResponse(
        message="El video ha sido eliminado exitosamente.",
        video_id=str(video_id),
    )
