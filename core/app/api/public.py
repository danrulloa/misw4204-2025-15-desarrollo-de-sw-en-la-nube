"""
Router de endpoints públicos
Endpoints para listar videos, votar y consultar rankings
"""

from fastapi import APIRouter, status, HTTPException, Query, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.database import get_session
from app.models.video import Video, VideoStatus
from app.models.vote import Vote
from app.schemas.vote import (
    PublicVideoResponse,
    VoteResponse,
    RankingResponse,
    RankingItemResponse
)
from app.schemas.common import ErrorResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, os

router = APIRouter(prefix="/public", tags=["Public"])


@router.get(
    "/videos",
    status_code=status.HTTP_200_OK,
    response_model=List[PublicVideoResponse],
    summary="Listar videos públicos",
    description="Lista todos los videos procesados disponibles para votación"
)
async def list_public_videos(
    city: Optional[str] = Query(None, description="Filtrar por ciudad"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Número de resultados a saltar"),
    db: AsyncSession = Depends(get_session)
) -> List[PublicVideoResponse]:
    """Lista videos públicos disponibles para votación"""

    stmt = (
        select(
            Video.id,
            Video.title,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city,
            Video.processed_path,
            func.count(Vote.id).label("votes_count")
        )
        .outerjoin(Vote, Vote.video_id == Video.id)
        .where(Video.status == VideoStatus.processed)
        .group_by(
            Video.id,
            Video.title,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city,
            Video.processed_path
        )
        .order_by(func.count(Vote.id).desc())
        .limit(limit)
        .offset(offset)
    )

    if city:
        stmt = stmt.where(Video.player_city.ilike(f"%{city}%"))

    result = await db.execute(stmt)
    videos = result.all()

    return [
        PublicVideoResponse(
            video_id=str(video.id),
            title=video.title,
            username=f"{video.player_first_name} {video.player_last_name}".strip(),
            city=video.player_city or "",
            processed_url=None,  # TODO: Implementar URL de descarga
            votes=video.votes_count
        )
        for video in videos
    ]


@router.get(
    "/videos/{video_id}",
    status_code=status.HTTP_200_OK,
    response_model=PublicVideoResponse,
    summary="Consultar video público",
    description="Obtiene el detalle de un video público específico"
)
async def get_public_video(
    video_id: str,
    db: AsyncSession = Depends(get_session)
) -> PublicVideoResponse:
    """Obtiene el detalle de un video público por su ID"""

    stmt = (
        select(
            Video.id,
            Video.title,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city,
            Video.processed_path,
            func.count(Vote.id).label("votes_count")
        )
        .outerjoin(Vote, Vote.video_id == Video.id)
        .where(Video.id == video_id)
        .where(Video.status == VideoStatus.processed)
        .group_by(
            Video.id,
            Video.title,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city,
            Video.processed_path
        )
    )

    result = await db.execute(stmt)
    video = result.one_or_none()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video no encontrado o no está disponible públicamente"
        )

    return PublicVideoResponse(
        video_id=str(video.id),
        title=video.title,
        username=f"{video.player_first_name} {video.player_last_name}".strip(),
        city=video.player_city or "",
        processed_url=None,  # TODO: Implementar URL de descarga
        votes=video.votes_count
    )




_bearer = HTTPBearer(auto_error=False)

def _get_user_id_from_token(creds: HTTPAuthorizationCredentials) -> str:
    """Extrae user_id del token JWT"""
    if not creds:
        raise HTTPException(status_code=401, detail="Se requiere autenticación")

    try:
        payload = jwt.decode(
            creds.credentials,
            os.getenv("ACCESS_TOKEN_SECRET_KEY", ""),
            algorithms=[os.getenv("ALGORITHM", "HS256")]
        )
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Token no contiene user_id")
        return str(user_id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")
#
#
@router.post(
    "/videos/{video_id}/vote",
    status_code=status.HTTP_201_CREATED,
    response_model=VoteResponse,
    summary="Votar por un video",
    description="Permite a un usuario registrado votar por un video público"
)
async def vote_video(
    video_id: str,
    db: AsyncSession = Depends(get_session),
    creds: HTTPAuthorizationCredentials = Depends(_bearer)
) -> VoteResponse:
    """Registra un voto para un video"""

    user_id = _get_user_id_from_token(creds)

    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado")

    if video.status != VideoStatus.processed:
        raise HTTPException(
            status_code=400,
            detail="Solo se puede votar por videos procesados"
        )

    existing = await db.execute(
        select(Vote).where(
            Vote.user_id == user_id,
            Vote.video_id == video_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya has votado por este video")

    try:
        vote = Vote(user_id=user_id, video_id=video_id)
        db.add(vote)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Ya has votado por este video")

    return VoteResponse(message="Voto registrado exitosamente")






@router.get(
    "/rankings",
    status_code=status.HTTP_200_OK,
    response_model=RankingResponse,
    summary="Consultar ranking",
    description="Obtiene el ranking de jugadores ordenado por número de votos"
)
async def get_rankings(
    city: Optional[str] = Query(None, description="Filtrar ranking por ciudad"),
    limit: int = Query(10, ge=1, le=100, description="Número de posiciones a mostrar"),
    db: AsyncSession = Depends(get_session)
) -> RankingResponse:
    """Obtiene el ranking de jugadores por votos totales"""

    stmt = (
        select(
            Video.user_id,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city,
            func.count(Vote.id).label("total_votes")
        )
        .join(Vote, Vote.video_id == Video.id)
        .where(Video.status == VideoStatus.processed)
        .group_by(
            Video.user_id,
            Video.player_first_name,
            Video.player_last_name,
            Video.player_city
        )
        .order_by(func.count(Vote.id).desc())
    )

    if city:
        stmt = stmt.where(Video.player_city == city)

    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    players = result.all()

    rankings = [
        RankingItemResponse(
            position=idx + 1,
            username=f"{p.player_first_name} {p.player_last_name}".strip(),
            city=p.player_city or "",
            votes=p.total_votes
        )
        for idx, p in enumerate(players)
    ]

    return RankingResponse(
        rankings=rankings,
        total=len(rankings)
    )
