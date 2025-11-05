"""
Router de gestión de videos
Endpoints para subir, listar, consultar y eliminar videos
"""

from fastapi import APIRouter, status, HTTPException, UploadFile, File, Form, Response, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
import os, jwt
from app.database import get_session
from app.models.video import Video
from app.services.uploads._init_ import get_upload_service
from app.services.uploads.base import UploadServicePort
from app.services.videos._init_ import get_video_query_service
from app.services.videos.base import VideoQueryServicePort
from app.services.storage.utils import storage_path_to_public_url
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from opentelemetry import trace
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

    tracer = trace.get_tracer("anb-core.api")
    # Create a child span under the request span to capture the upload service call
    with tracer.start_as_current_span("videos.upload") as span:
        span.set_attribute("enduser.id", user_id)
        span.set_attribute("video.title", title)
        if getattr(video_file, "filename", None):
            span.set_attribute("video.filename", video_file.filename)
        if getattr(video_file, "content_type", None):
            span.set_attribute("video.content_type", video_file.content_type)

        service: UploadServicePort = get_upload_service()
        try:
            video, correlation_id = await service.upload(
                user_id=user_id,
                title=title,
                upload_file=video_file,
                user_info=user_info,
                db=db,
            )
            span.set_attribute("task.correlation_id", correlation_id)
        except Exception as e:
            # Record exception details on the span and re-raise
            span.record_exception(e)
            span.set_attribute("error", True)
            raise

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
    service: VideoQueryServicePort = Depends(get_video_query_service),
    limit: int = 20,
    offset: int = 0,
) -> List[VideoListItemResponse]:
    user_id = _current_user_id(creds)
    videos = await service.list_user_videos(
        user_id=user_id,
        limit=limit,
        offset=offset,
        db=db,
    )

    items: List[VideoListItemResponse] = []
    for v in videos:
        items.append(
            VideoListItemResponse(
                video_id=str(v.id),
                title=v.title,
                status=v.status,
                uploaded_at=v.created_at,
                processed_at=v.processed_at,
                processed_url=storage_path_to_public_url(v.processed_path),
            )
        )
    return items


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
    service: VideoQueryServicePort = Depends(get_video_query_service),
) -> VideoResponse:
    user_id = _current_user_id(creds)
    video = await service.get_user_video(user_id=user_id, video_id=video_id, db=db)

    return VideoResponse(
        video_id=str(video.id),
        title=video.title,
        status=video.status,
        uploaded_at=video.created_at,
        processed_at=video.processed_at,
        original_url=storage_path_to_public_url(video.original_path),
        processed_url=storage_path_to_public_url(video.processed_path),
        votes=0,
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
    service: VideoQueryServicePort = Depends(get_video_query_service),
) -> VideoDeleteResponse:
    user_id = _current_user_id(creds)
    deleted_id = await service.delete_user_video(user_id=user_id, video_id=video_id, db=db)

    return VideoDeleteResponse(
        message="El video ha sido eliminado exitosamente.",
        video_id=str(deleted_id),
    )
