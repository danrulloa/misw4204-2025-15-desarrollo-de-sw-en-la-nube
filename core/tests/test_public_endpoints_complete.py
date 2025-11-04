import pytest
from types import SimpleNamespace

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

import app.api.public as public_mod
from app.services.public_videos.base import PublicVideoRecord, RankingRecord


class _StubPublicService:
    def __init__(self):
        self.list_params = None
        self.get_params = None
        self.vote_params = None
        self.rank_params = None
        self.list_response = []
        self.get_response = None
        self.rank_response = []

    async def list_videos(self, **kwargs):
        self.list_params = kwargs
        return self.list_response

    async def get_video(self, **kwargs):
        self.get_params = kwargs
        if self.get_response is None:
            raise HTTPException(status_code=404, detail="not found")
        return self.get_response

    async def register_vote(self, **kwargs):
        self.vote_params = kwargs

    async def get_rankings(self, **kwargs):
        self.rank_params = kwargs
        return self.rank_response


@pytest.fixture
def stub_service(monkeypatch):
    stub = _StubPublicService()
    monkeypatch.setattr(public_mod, "get_public_video_service", lambda: stub)
    return stub


@pytest.mark.asyncio
async def test_list_public_videos_maps_response(monkeypatch, stub_service):
    stub_service.list_response = [
        PublicVideoRecord(
            video_id="vid-1",
            title="Video 1",
            first_name="John",
            last_name="Doe",
            city="Bogotá",
            processed_path="/processed/vid-1.mp4",
            votes=7,
        )
    ]

    monkeypatch.setattr(
        public_mod, "storage_path_to_public_url", lambda path: f"url://{path}"
    )

    fake_db = SimpleNamespace()
    result = await public_mod.list_public_videos(
        db=fake_db,
        limit=10,
        offset=2,
        service=stub_service,
    )

    assert len(result) == 1
    item = result[0]
    assert item.video_id == "vid-1"
    assert item.player_name == "John Doe"
    assert item.city == "Bogotá"
    assert item.processed_url == "url:///processed/vid-1.mp4"
    assert item.votes == 7

    assert stub_service.list_params["limit"] == 10
    assert stub_service.list_params["offset"] == 2
    assert stub_service.list_params["db"] is fake_db


@pytest.mark.asyncio
async def test_get_public_video_returns_schema(monkeypatch, stub_service):
    stub_service.get_response = PublicVideoRecord(
        video_id="vid-1",
        title="Video 1",
        first_name="Ana",
        last_name="Smith",
        city=None,
        processed_path="s3://bucket/key.mp4",
        votes=12,
    )
    monkeypatch.setattr(public_mod, "storage_path_to_public_url", lambda path: "https://media/key.mp4")

    fake_db = SimpleNamespace()
    result = await public_mod.get_public_video(
        "vid-1",
        db=fake_db,
        service=stub_service,
    )

    assert result.video_id == "vid-1"
    assert result.player_name == "Ana Smith"
    assert result.city == ""
    assert result.processed_url == "https://media/key.mp4"
    assert result.votes == 12
    assert stub_service.get_params["video_id"] == "vid-1"
    assert stub_service.get_params["db"] is fake_db


@pytest.mark.asyncio
async def test_vote_video_uses_service(monkeypatch, stub_service):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    monkeypatch.setattr(public_mod, "_get_user_id_from_token", lambda c: "user-123")

    fake_db = SimpleNamespace()
    response = await public_mod.vote_video(
        "vid-55",
        db=fake_db,
        creds=creds,
        service=stub_service,
    )

    assert response.message.startswith("Voto registrado")
    assert stub_service.vote_params["video_id"] == "vid-55"
    assert stub_service.vote_params["user_id"] == "user-123"
    assert stub_service.vote_params["db"] is fake_db


@pytest.mark.asyncio
async def test_get_rankings_returns_positions(stub_service):
    stub_service.rank_response = [
        RankingRecord(username="John Doe", city="Bogotá", votes=10),
        RankingRecord(username="Ana Smith", city=None, votes=9),
    ]

    fake_db = SimpleNamespace()
    result = await public_mod.get_rankings(
        db=fake_db,
        limit=5,
        service=stub_service,
    )

    assert result.total == 2
    assert result.rankings[0].position == 1
    assert result.rankings[0].username == "John Doe"
    assert result.rankings[1].position == 2
    assert result.rankings[1].city == ""
    assert stub_service.rank_params["db"] is fake_db
