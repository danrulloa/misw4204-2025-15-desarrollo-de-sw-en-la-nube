"""
Tests completos para public.py con mocking de base de datos
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import jwt
import os

from app.api.public import (
    list_public_videos, 
    get_public_video, 
    vote_video, 
    get_rankings,
    _get_user_id_from_token
)
from app.schemas.vote import PublicVideoResponse, VoteResponse, RankingResponse, RankingItemResponse


class TestPublicEndpointsComplete:
    """Tests completos para endpoints públicos con mocking de BD"""

    @pytest.mark.asyncio
    async def test_list_public_videos_success(self):
        """Test que list_public_videos retorna videos correctamente"""
        # Mock de datos de respuesta
        mock_videos = [
            MagicMock(
                id="video1",
                title="Video 1",
                player_first_name="John",
                player_last_name="Doe",
                player_city="Bogotá",
                processed_path="/processed/video1.mp4",
                votes_count=5
            ),
            MagicMock(
                id="video2", 
                title="Video 2",
                player_first_name="Jane",
                player_last_name="Smith",
                player_city="Medellín",
                processed_path="/processed/video2.mp4",
                votes_count=3
            )
        ]
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_videos
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        # Ejecutar función con parámetros explícitos
        result = await list_public_videos(limit=50, offset=0, db=mock_db)
        
        # Verificar resultado
        assert len(result) == 2
        assert isinstance(result[0], PublicVideoResponse)
        assert result[0].video_id == "video1"
        assert result[0].title == "Video 1"
        assert result[0].player_name == "John Doe"  # Usar player_name en lugar de username
        assert result[0].city == "Bogotá"
        assert result[0].votes == 5

    @pytest.mark.asyncio
    async def test_list_public_videos_with_city_filter(self):
        """Test que list_public_videos filtra por ciudad"""
        mock_videos = [
            MagicMock(
                id="video1",
                title="Video 1",
                player_first_name="John",
                player_last_name="Doe",
                player_city="Bogotá",
                processed_path="/processed/video1.mp4",
                votes_count=5
            )
        ]
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_videos
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        # Ejecutar función con filtro de ciudad
        result = await list_public_videos(city="Bogotá", limit=50, offset=0, db=mock_db)
        
        # Verificar que se ejecutó la consulta
        mock_db.execute.assert_called_once()
        assert len(result) == 1
        assert result[0].city == "Bogotá"

    @pytest.mark.asyncio
    async def test_list_public_videos_empty_result(self):
        """Test que list_public_videos maneja resultado vacío"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await list_public_videos(limit=50, offset=0, db=mock_db)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_list_public_videos_with_limit_offset(self):
        """Test que list_public_videos respeta limit y offset"""
        mock_videos = []
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_videos
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        # Ejecutar función con limit y offset
        result = await list_public_videos(limit=10, offset=5, db=mock_db)
        
        # Verificar que se ejecutó la consulta
        mock_db.execute.assert_called_once()
        assert result == []

    @pytest.mark.asyncio
    async def test_get_public_video_success(self):
        """Test que get_public_video retorna video correctamente"""
        mock_video = MagicMock(
            id="video1",
            title="Video 1",
            player_first_name="John",
            player_last_name="Doe",
            player_city="Bogotá",
            processed_path="/processed/video1.mp4",
            votes_count=5
        )
        
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = mock_video
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await get_public_video("video1", db=mock_db)
        
        assert isinstance(result, PublicVideoResponse)
        assert result.video_id == "video1"
        assert result.title == "Video 1"
        assert result.player_name == "John Doe"  # Usar player_name en lugar de username
        assert result.city == "Bogotá"
        assert result.votes == 5

    @pytest.mark.asyncio
    async def test_get_public_video_not_found(self):
        """Test que get_public_video maneja video no encontrado"""
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await get_public_video("nonexistent", db=mock_db)
        
        assert exc_info.value.status_code == 404
        assert "Video no encontrado" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_vote_video_success(self):
        """Test que vote_video registra voto correctamente"""
        mock_video = MagicMock()
        mock_video.id = "video1"
        mock_video.status = "processed"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [mock_result, mock_existing_result]
        
        mock_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        
        with patch('app.api.public._get_user_id_from_token') as mock_get_user:
            mock_get_user.return_value = "user123"
            
            result = await vote_video("video1", db=mock_db, creds=mock_creds)
            
            assert isinstance(result, VoteResponse)
            assert result.message == "Voto registrado exitosamente"
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_vote_video_not_found(self):
        """Test que vote_video maneja video no encontrado"""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        mock_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        
        with patch('app.api.public._get_user_id_from_token') as mock_get_user:
            mock_get_user.return_value = "user123"
            
            with pytest.raises(HTTPException) as exc_info:
                await vote_video("nonexistent", db=mock_db, creds=mock_creds)
            
            assert exc_info.value.status_code == 404
            assert "Video no encontrado" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_vote_video_not_processed(self):
        """Test que vote_video rechaza video no procesado"""
        mock_video = MagicMock()
        mock_video.id = "video1"
        mock_video.status = "uploaded"  # No procesado
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        mock_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        
        with patch('app.api.public._get_user_id_from_token') as mock_get_user:
            mock_get_user.return_value = "user123"
            
            with pytest.raises(HTTPException) as exc_info:
                await vote_video("video1", db=mock_db, creds=mock_creds)
            
            assert exc_info.value.status_code == 400
            assert "Solo se puede votar por videos procesados" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_vote_video_already_voted(self):
        """Test que vote_video rechaza voto duplicado"""
        mock_video = MagicMock()
        mock_video.id = "video1"
        mock_video.status = "processed"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = MagicMock()  # Ya existe voto
        
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [mock_result, mock_existing_result]
        
        mock_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        
        with patch('app.api.public._get_user_id_from_token') as mock_get_user:
            mock_get_user.return_value = "user123"
            
            with pytest.raises(HTTPException) as exc_info:
                await vote_video("video1", db=mock_db, creds=mock_creds)
            
            assert exc_info.value.status_code == 400
            assert "Ya has votado por este video" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_vote_video_integrity_error(self):
        """Test que vote_video maneja error de integridad"""
        from sqlalchemy.exc import IntegrityError
        
        mock_video = MagicMock()
        mock_video.id = "video1"
        mock_video.status = "processed"
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_video
        
        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None
        
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [mock_result, mock_existing_result]
        mock_db.commit.side_effect = IntegrityError("statement", "params", "orig")
        
        mock_creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid.token")
        
        with patch('app.api.public._get_user_id_from_token') as mock_get_user:
            mock_get_user.return_value = "user123"
            
            with pytest.raises(HTTPException) as exc_info:
                await vote_video("video1", db=mock_db, creds=mock_creds)
            
            assert exc_info.value.status_code == 400
            assert "Ya has votado por este video" in exc_info.value.detail
            mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_rankings_success(self):
        """Test que get_rankings retorna ranking correctamente"""
        mock_players = [
            MagicMock(
                user_id="user1",
                player_first_name="John",
                player_last_name="Doe",
                player_city="Bogotá",
                total_votes=10
            ),
            MagicMock(
                user_id="user2",
                player_first_name="Jane",
                player_last_name="Smith",
                player_city="Medellín",
                total_votes=8
            )
        ]
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_players
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await get_rankings(limit=10, db=mock_db)
        
        assert isinstance(result, RankingResponse)
        assert len(result.rankings) == 2
        assert result.total == 2
        
        # Verificar primer lugar
        assert result.rankings[0].position == 1
        assert result.rankings[0].username == "John Doe"
        assert result.rankings[0].city == "Bogotá"
        assert result.rankings[0].votes == 10
        
        # Verificar segundo lugar
        assert result.rankings[1].position == 2
        assert result.rankings[1].username == "Jane Smith"
        assert result.rankings[1].city == "Medellín"
        assert result.rankings[1].votes == 8

    @pytest.mark.asyncio
    async def test_get_rankings_with_city_filter(self):
        """Test que get_rankings filtra por ciudad"""
        mock_players = [
            MagicMock(
                user_id="user1",
                player_first_name="John",
                player_last_name="Doe",
                player_city="Bogotá",
                total_votes=10
            )
        ]
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_players
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await get_rankings(city="Bogotá", limit=10, db=mock_db)
        
        assert len(result.rankings) == 1
        assert result.rankings[0].city == "Bogotá"

    @pytest.mark.asyncio
    async def test_get_rankings_with_limit(self):
        """Test que get_rankings respeta el límite"""
        mock_players = []
        
        mock_result = MagicMock()
        mock_result.all.return_value = mock_players
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await get_rankings(limit=5, db=mock_db)
        
        assert result.total == 0
        assert len(result.rankings) == 0

    @pytest.mark.asyncio
    async def test_get_rankings_empty_result(self):
        """Test que get_rankings maneja resultado vacío"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result
        
        result = await get_rankings(limit=10, db=mock_db)
        
        assert isinstance(result, RankingResponse)
        assert result.total == 0
        assert result.rankings == []
