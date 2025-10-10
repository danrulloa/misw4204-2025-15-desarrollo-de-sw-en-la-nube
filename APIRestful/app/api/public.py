"""
Router de endpoints públicos
Endpoints para listar videos, votar y consultar rankings
"""

from fastapi import APIRouter, status, HTTPException, Query
from typing import List, Optional
from app.schemas.vote import (
    PublicVideoResponse,
    VoteResponse,
    RankingResponse
)
from app.schemas.common import ErrorResponse

router = APIRouter(prefix="/api/public", tags=["Public"])


@router.get(
    "/videos",
    status_code=status.HTTP_200_OK,
    response_model=List[PublicVideoResponse],
    summary="Listar videos públicos",
    description="Lista todos los videos procesados disponibles para votación",
    responses={
        200: {
            "description": "Lista de videos públicos obtenida",
            "model": List[PublicVideoResponse]
        }
    }
)
async def list_public_videos(
    city: Optional[str] = Query(None, description="Filtrar por ciudad"),
    limit: int = Query(50, ge=1, le=100, description="Número máximo de resultados"),
    offset: int = Query(0, ge=0, description="Número de resultados a saltar")
) -> List[PublicVideoResponse]:
    """
    Lista videos públicos disponibles para votación.
    
    Características:
    - Solo muestra videos en estado "processed"
    - Incluye información del jugador
    - Muestra número de votos actual
    - Soporta paginación
    - Filtro opcional por ciudad
    """
    # TODO: Implementar cuando se tenga DB
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )


@router.post(
    "/videos/{video_id}/vote",
    status_code=status.HTTP_200_OK,
    response_model=VoteResponse,
    summary="Votar por un video",
    description="Permite a un usuario registrado votar por un video público",
    responses={
        200: {
            "description": "Voto registrado exitosamente",
            "model": VoteResponse
        },
        400: {
            "description": "Ya has votado por este video",
            "model": ErrorResponse
        },
        401: {
            "description": "Falta de autenticación",
            "model": ErrorResponse
        },
        404: {
            "description": "Video no encontrado",
            "model": ErrorResponse
        }
    }
)
async def vote_video(video_id: str) -> VoteResponse:
    """
    Registra un voto para un video.
    
    Reglas:
    - Un usuario solo puede votar una vez por video
    - Un usuario puede votar por múltiples videos
    - Solo se puede votar por videos en estado "processed"
    - Requiere autenticación
    """
    # TODO: Implementar cuando se tenga DB y auth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )


@router.get(
    "/rankings",
    status_code=status.HTTP_200_OK,
    response_model=RankingResponse,
    summary="Consultar ranking",
    description="Obtiene el ranking de jugadores ordenado por número de votos",
    responses={
        200: {
            "description": "Ranking obtenido exitosamente",
            "model": RankingResponse
        },
        400: {
            "description": "Parámetro inválido en la consulta",
            "model": ErrorResponse
        }
    }
)
async def get_rankings(
    city: Optional[str] = Query(None, description="Filtrar ranking por ciudad"),
    limit: int = Query(10, ge=1, le=100, description="Número de posiciones a mostrar")
) -> RankingResponse:
    """
    Obtiene el ranking de jugadores por votos.
    
    Características:
    - Ordenado por número de votos (descendente)
    - Incluye posición, nombre, ciudad y votos
    - Filtro opcional por ciudad
    - Soporta paginación
    - Se recomienda usar caché (Redis) para optimizar
    """
    # TODO: Implementar cuando se tenga DB
    # TODO: Considerar implementar caché con Redis para mejorar performance
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint pendiente de implementación. Esperando decisiones de DB."
    )
