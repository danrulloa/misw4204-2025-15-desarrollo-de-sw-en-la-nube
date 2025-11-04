"""
Router de endpoints públicos
Endpoints para listar videos, votar y consultar rankings
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import jwt
import os

from app.database import get_session
from app.schemas.vote import (
    PublicVideoResponse,
    RankingItemResponse,
    RankingResponse,
    VoteResponse,
)
from app.schemas.common import ErrorResponse
from app.services.public_videos.base import PublicVideoServicePort
from app.services.public_videos._init_ import get_public_video_service
from app.services.storage.utils import storage_path_to_public_url

router = APIRouter(prefix="/public", tags=["Public"])
_bearer = HTTPBearer(auto_error=False)


@router.get(
    "/videos",
    status_code=status.HTTP_200_OK,
    response_model=List[PublicVideoResponse],
    summary="Listar videos públicos",
    description="Lista todos los videos procesados disponibles para votación",
)
async def list_public_videos(
    city: Optional[str] = Query(None, description="Filtrar por ciudad"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Número de resultados a saltar"),
    db: AsyncSession = Depends(get_session),
    service: PublicVideoServicePort = Depends(get_public_video_service),
) -> List[PublicVideoResponse]:
    """Lista videos públicos disponibles para votación."""

    records = await service.list_videos(city=city, limit=limit, offset=offset, db=db)

    public_videos: List[PublicVideoResponse] = []
    for record in records:
        public_videos.append(
            PublicVideoResponse(
                video_id=record.video_id,
                title=record.title,
                player_name=record.username,
                city=record.city or "",
                processed_url=storage_path_to_public_url(record.processed_path),
                votes=record.votes,
            )
        )
    return public_videos


@router.get(
    "/videos/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublicVideoResponse,
    summary="Consultar video público",
    description="Obtiene el detalle de un video público específico",
)
async def get_public_video(
    video_id: str,
    db: AsyncSession = Depends(get_session),
    service: PublicVideoServicePort = Depends(get_public_video_service),
) -> PublicVideoResponse:
    """Obtiene el detalle de un video público por su ID."""

    record = await service.get_video(video_id=video_id, db=db)
    return PublicVideoResponse(
        video_id=record.video_id,
        title=record.title,
        player_name=record.username,
        city=record.city or "",
        processed_url=storage_path_to_public_url(record.processed_path),
        votes=record.votes,
    )


def _get_user_id_from_token(creds: HTTPAuthorizationCredentials) -> str:
    """Extrae user_id del token JWT"""
    if not creds:
        raise HTTPException(status_code=401, detail="Se requiere autenticación")

    try:
        payload = jwt.decode(
            creds.credentials,
            os.getenv("ACCESS_TOKEN_SECRET_KEY", ""),
            algorithms=[os.getenv("ALGORITHM", "HS256")],
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Token no contiene user_id")
        return str(user_id)
    except Exception as e:  # pragma: no cover - we re-raise as HTTPException
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")


@router.post(
    "/videos/{video_id}/vote",
    status_code=status.HTTP_201_CREATED,
    response_model=VoteResponse,
    summary="Votar por un video",
    description="Permite a un usuario registrado votar por un video público",
    responses={status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse}},
)
async def vote_video(
    video_id: str,
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    service: PublicVideoServicePort = Depends(get_public_video_service),
) -> VoteResponse:
    """Registra un voto para un video."""

    user_id = _get_user_id_from_token(creds)
    await service.register_vote(video_id=video_id, user_id=user_id, db=db)
    return VoteResponse(message="Voto registrado exitosamente")


@router.get(
    "/rankings",
    status_code=status.HTTP_200_OK,
    response_model=RankingResponse,
    summary="Consultar ranking",
    description="Obtiene el ranking de jugadores ordenado por número de votos",
)
async def get_rankings(
    city: Optional[str] = Query(None, description="Filtrar ranking por ciudad"),
    limit: int = Query(10, ge=1, le=100, description="Número de posiciones a mostrar"),
    db: AsyncSession = Depends(get_session),
    service: PublicVideoServicePort = Depends(get_public_video_service),
) -> RankingResponse:
    """Obtiene el ranking de jugadores por votos totales."""

    records = await service.get_rankings(city=city, limit=limit, db=db)
    ranking_items = [
        RankingItemResponse(
            position=index + 1,
            username=record.username,
            city=record.city or "",
            votes=record.votes,
        )
        for index, record in enumerate(records)
    ]
    return RankingResponse(rankings=ranking_items, total=len(ranking_items))
