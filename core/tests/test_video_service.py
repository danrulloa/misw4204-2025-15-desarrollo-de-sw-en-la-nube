import uuid

import uuid

import pytest

from fastapi import HTTPException

from app.models.video import Video, VideoStatus
from app.services.storage import utils as storage_utils
from app.services.videos.local import VideoQueryService


class _DummySession:
    def __init__(self, *, list_result=None, get_result=None):
        self.list_result = list_result or []
        self.get_result = get_result
        self.last_stmt = None
        self.deleted = None
        self.committed = False

    async def execute(self, stmt):
        self.last_stmt = stmt

        class _Result:
            def __init__(self, list_result, single_result):
                self._list_result = list_result
                self._single_result = single_result

            def scalars(self):
                class _Scalar:
                    def __init__(self, list_result, single_result):
                        self.list_result = list_result
                        self.single_result = single_result

                    def all(self):
                        if self.single_result is not None:
                            return [self.single_result]
                        return list(self.list_result)

                return _Scalar(self._list_result, self._single_result)

            def scalar_one_or_none(self):
                return self._single_result

        return _Result(self.list_result, self.get_result)

    async def delete(self, obj):
        self.deleted = obj

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_list_user_videos_returns_videos():
    service = VideoQueryService()
    videos = [
        Video(
            id=uuid.uuid4(),
            user_id="user",
            title="Test",
            original_filename="test.mp4",
            original_path="/uploads/test.mp4",
            status=VideoStatus.uploaded,
        )
    ]
    session = _DummySession(list_result=videos)

    result = await service.list_user_videos(user_id="user", limit=10, offset=0, db=session)

    assert result == videos
    assert session.last_stmt is not None


@pytest.mark.asyncio
async def test_get_user_video_returns_video():
    service = VideoQueryService()
    video = Video(
        id=uuid.uuid4(),
        user_id="user",
        title="Detail",
        original_filename="detail.mp4",
        original_path="/uploads/detail.mp4",
        status=VideoStatus.uploaded,
    )
    session = _DummySession(get_result=video)

    result = await service.get_user_video(user_id="user", video_id=str(video.id), db=session)

    assert result is video
    assert session.last_stmt is not None


@pytest.mark.asyncio
async def test_get_user_video_not_found():
    service = VideoQueryService()
    session = _DummySession(get_result=None)

    with pytest.raises(HTTPException) as exc:
        await service.get_user_video(user_id="user", video_id="missing", db=session)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_video_forbidden():
    service = VideoQueryService()
    video = Video(
        id=uuid.uuid4(),
        user_id="other",
        title="Nope",
        original_filename="nope.mp4",
        original_path="/uploads/nope.mp4",
        status=VideoStatus.uploaded,
    )
    session = _DummySession(get_result=video)

    with pytest.raises(HTTPException) as exc:
        await service.get_user_video(user_id="user", video_id=str(video.id), db=session)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_video_removes_files(tmp_path, monkeypatch):
    service = VideoQueryService()
    upload_dir = tmp_path / "uploads"
    processed_dir = tmp_path / "processed"
    upload_dir.mkdir()
    processed_dir.mkdir()
    monkeypatch.setattr(storage_utils.settings, "UPLOAD_DIR", str(upload_dir))
    monkeypatch.setattr(storage_utils.settings, "PROCESSED_DIR", str(processed_dir))

    video = Video(
        id=uuid.uuid4(),
        user_id="user",
        title="Delete",
        original_filename="del.mp4",
        original_path="/uploads/del.mp4",
        processed_path="/processed/del.m3u8",
        status=VideoStatus.uploaded,
    )
    orig = upload_dir / "del.mp4"
    proc = processed_dir / "del.m3u8"
    orig.write_bytes(b"x")
    proc.write_bytes(b"y")

    session = _DummySession(get_result=video)

    deleted_id = await service.delete_user_video(user_id="user", video_id=str(video.id), db=session)

    assert deleted_id == str(video.id)
    assert session.deleted is video
    assert session.committed is True
    assert not orig.exists()
    assert not proc.exists()
