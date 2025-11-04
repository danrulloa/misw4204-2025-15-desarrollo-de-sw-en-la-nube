import pytest
from types import SimpleNamespace

from fastapi import HTTPException

from app.models.video import VideoStatus
from app.services.public_videos.local import PublicVideoService


class _Result:
    def __init__(self, *, rows=None, scalar=None):
        self._rows = rows or []
        self._scalar = scalar

    def all(self):
        return list(self._rows)

    def one_or_none(self):
        if self._rows:
            return self._rows[0]
        return None

    def scalar_one_or_none(self):
        return self._scalar


class _SeqSession:
    def __init__(self, results):
        self._results = list(results)
        self.added = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, stmt):
        if not self._results:
            raise AssertionError("Unexpected execute call")
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_list_videos_returns_records():
    service = PublicVideoService()
    row = SimpleNamespace(
        id="vid-1",
        title="Video",
        player_first_name="Ana",
        player_last_name="Lopez",
        player_city="Cali",
        processed_path="/processed/vid.mp4",
        votes_count=5,
    )
    session = _SeqSession([_Result(rows=[row])])

    records = await service.list_videos(city=None, limit=10, offset=0, db=session)

    assert len(records) == 1
    record = records[0]
    assert record.video_id == "vid-1"
    assert record.username == "Ana Lopez"
    assert record.city == "Cali"
    assert record.processed_path == "/processed/vid.mp4"
    assert record.votes == 5


@pytest.mark.asyncio
async def test_get_video_not_found():
    service = PublicVideoService()
    session = _SeqSession([_Result(rows=[])])

    with pytest.raises(HTTPException) as exc:
        await service.get_video(video_id="missing", db=session)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_register_vote_success():
    service = PublicVideoService()
    video = SimpleNamespace(id="vid-1", status=VideoStatus.processed)
    session = _SeqSession(
        [
            _Result(scalar=video),  # fetch video
            _Result(scalar=None),  # existing vote
        ]
    )

    await service.register_vote(video_id="vid-1", user_id="user-1", db=session)

    assert session.added, "vote should be added to session"
    assert session.commits == 1


@pytest.mark.asyncio
async def test_register_vote_duplicate():
    service = PublicVideoService()
    video = SimpleNamespace(id="vid-1", status=VideoStatus.processed)
    existing_vote = object()
    session = _SeqSession(
        [
            _Result(scalar=video),
            _Result(scalar=existing_vote),
        ]
    )

    with pytest.raises(HTTPException) as exc:
        await service.register_vote(video_id="vid-1", user_id="user-1", db=session)

    assert exc.value.status_code == 400
    assert "Ya has votado" in exc.value.detail


@pytest.mark.asyncio
async def test_get_rankings_returns_ordered_records():
    service = PublicVideoService()
    rows = [
        SimpleNamespace(player_first_name="Ana", player_last_name="Lopez", player_city="Cali", total_votes=10),
        SimpleNamespace(player_first_name="John", player_last_name="Doe", player_city=None, total_votes=8),
    ]
    session = _SeqSession([_Result(rows=rows)])

    records = await service.get_rankings(city=None, limit=5, db=session)

    assert len(records) == 2
    assert records[0].username == "Ana Lopez"
    assert records[1].city is None
    assert records[1].votes == 8
