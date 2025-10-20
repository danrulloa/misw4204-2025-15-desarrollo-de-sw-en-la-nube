"""
Tests para schemas de votación
"""

import pytest
from pydantic import ValidationError
from app.schemas.vote import (
    VoteResponse,
    PublicVideoResponse,
    RankingItemResponse,
    RankingResponse
)


class TestVoteResponse:
    """Tests para el schema de respuesta de voto"""
    
    def test_valid_vote_response(self):
        """Test con respuesta válida"""
        response = VoteResponse(message="Voto registrado exitosamente")
        assert response.message == "Voto registrado exitosamente"


class TestPublicVideoResponse:
    """Tests para el schema de video público"""
    
    def test_valid_public_video(self):
        """Test con video público válido"""
        video = PublicVideoResponse(
            video_id="abc123",
            title="Tiros de tres",
            player_name="John Doe",
            city="Bogotá",
            processed_url="http://example.com/video.mp4",
            votes=125
        )
        assert video.video_id == "abc123"
        assert video.player_name == "John Doe"
        assert video.city == "Bogotá"
        assert video.votes == 125
    
    def test_default_votes_zero(self):
        """Test que votes tiene valor por defecto 0"""
        video = PublicVideoResponse(
            video_id="abc123",
            title="Test",
            player_name="John",
            city="Bogotá",
            processed_url="http://example.com/video.mp4"
        )
        assert video.votes == 0


class TestRankingItemResponse:
    """Tests para el schema de item de ranking"""
    
    def test_valid_ranking_item(self):
        """Test con item de ranking válido"""
        item = RankingItemResponse(
            position=1,
            username="superplayer",
            city="Bogotá",
            votes=1530
        )
        assert item.position == 1
        assert item.username == "superplayer"
        assert item.votes == 1530
    
    def test_missing_required_fields(self):
        """Test con campos requeridos faltantes"""
        with pytest.raises(ValidationError):
            RankingItemResponse(position=1, username="test")


class TestRankingResponse:
    """Tests para el schema de respuesta de ranking"""
    
    def test_valid_ranking_response(self):
        """Test con ranking válido"""
        rankings = [
            RankingItemResponse(
                position=1,
                username="player1",
                city="Bogotá",
                votes=100
            ),
            RankingItemResponse(
                position=2,
                username="player2",
                city="Medellín",
                votes=90
            )
        ]
        response = RankingResponse(rankings=rankings, total=2)
        assert len(response.rankings) == 2
        assert response.total == 2
        assert response.rankings[0].position == 1
    
    def test_empty_rankings(self):
        """Test con ranking vacío"""
        response = RankingResponse(rankings=[], total=0)
        assert len(response.rankings) == 0
        assert response.total == 0
