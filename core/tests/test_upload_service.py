"""Tests unitarios para LocalUploadService."""

import io
import uuid

import pytest
from fastapi import HTTPException, UploadFile

from app.models.video import VideoStatus
from app.services.uploads import local as uploads_local
from app.services.uploads.local import LocalUploadService


class _StubSession:
    def __init__(self, store: dict | None = None):
        self.added = None
        self.commits = 0
        self.refresh_calls = 0
        self.flush_calls = 0
        self.rollback_calls = 0
        self.store = store if store is not None else {}

    def add(self, obj):
        self.added = obj

    async def commit(self):
        self.commits += 1

    async def flush(self):
        self.flush_calls += 1
        # Simular asignación de ID en flush (similar a refresh)
        if getattr(self.added, "id", None) is None:
            self.added.id = uuid.uuid4()
        if self.added:
            self.store[self.added.id] = self.added

    async def rollback(self):
        self.rollback_calls += 1

    async def refresh(self, obj):
        self.refresh_calls += 1
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        if obj:
            self.store[obj.id] = obj

    async def get(self, _model, key):
        return self.store.get(key)


class _SessionCtx:
    def __init__(self, session: _StubSession):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _StubStorage:
    def __init__(self, *, should_fail: Exception | None = None):
        self.should_fail = should_fail
        self.calls = []

    def save(self, fileobj, filename, content_type):
        if self.should_fail:
            raise self.should_fail
        self.calls.append((fileobj, filename, content_type))
        return f"/uploads/{filename}"


class _StubPublisher:
    def __init__(self, *, should_fail: Exception | None = None):
        self.should_fail = should_fail
        self.payload = None
        self.closed = False

    def publish_video(self, payload):
        if self.should_fail:
            raise self.should_fail
        self.payload = payload

    def close(self):
        self.closed = True


class _FakeUploadFile:
    def __init__(self, name: str, data: bytes, content_type: str):
        self.filename = name
        self.content_type = content_type
        self.file = io.BytesIO(data)


class _DiskUploadFile:
    def __init__(self, path):
        self.filename = path.name
        self.content_type = "video/mp4"
        self.file = open(path, "rb")


def _make_file(name: str = "clip.mp4", data: bytes = b"video") -> UploadFile:
    return _FakeUploadFile(name, data, "video/mp4")  # type: ignore[return-value]


def _build_service(monkeypatch, tmp_path, *, process_inline: bool, storage_backend: str = "local"):
    shared_store: dict = {}
    pipeline_session = _StubSession(store=shared_store)

    monkeypatch.setattr(uploads_local.settings, "ALLOWED_VIDEO_FORMATS", {"mp4"})
    monkeypatch.setattr(uploads_local.settings, "MAX_UPLOAD_SIZE_MB", 100)
    monkeypatch.setattr(uploads_local.settings, "WORKER_INPUT_PREFIX", "/worker/in")
    monkeypatch.setattr(uploads_local.settings, "STORAGE_BACKEND", storage_backend)
    monkeypatch.setattr(uploads_local.settings, "S3_BUCKET", "tests-bucket")
    monkeypatch.setattr(uploads_local.settings, "UPLOAD_STAGING_DIR", tmp_path.as_posix())
    monkeypatch.setattr(uploads_local, "SessionLocal", lambda: _SessionCtx(pipeline_session))

    svc = LocalUploadService(process_inline=process_inline, staging_root=tmp_path)
    svc._test_store = shared_store  # type: ignore[attr-defined]
    svc._test_pipeline_session = pipeline_session  # type: ignore[attr-defined]
    return svc


@pytest.fixture
def service(monkeypatch, tmp_path):
    return _build_service(monkeypatch, tmp_path, process_inline=True)


@pytest.fixture
def service_async(monkeypatch, tmp_path):
    return _build_service(monkeypatch, tmp_path, process_inline=False)


@pytest.mark.asyncio
async def test_upload_service_happy_path(service, monkeypatch):
    storage = _StubStorage()
    publisher = _StubPublisher()
    monkeypatch.setattr(uploads_local, "get_storage", lambda: storage)
    monkeypatch.setattr(uploads_local, "RabbitPublisher", lambda: publisher)

    db = _StubSession(store=service._test_store)  # type: ignore[attr-defined]
    user_info = {"first_name": "Ana", "last_name": "Player", "city": "Bogota"}

    video, correlation = await service.upload(
        user_id="user-123",
        title="Gran jugada",
        upload_file=_make_file(),
        user_info=user_info,
        db=db,
    )

    assert len(storage.calls) == 1
    _, saved_name, saved_type = storage.calls[0]
    assert saved_name.endswith(".mp4")
    assert saved_type == "video/mp4"

    assert db.added is video
    assert db.commits == 1  # Commit inicial
    assert db.flush_calls == 1  # Flush para obtener ID
    assert db.refresh_calls == 0  # Ya no necesitamos refresh
    assert video.status is VideoStatus.processing
    assert video.correlation_id == correlation
    assert video.player_first_name == "Ana"

    assert publisher.payload == {
        "video_id": str(video.id),
        "input_path": video.original_path.replace("/uploads", "/worker/in", 1),
        "correlation_id": correlation,
    }
    assert publisher.closed is True
    assert service._test_pipeline_session.commits == 1  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_upload_service_storage_failure(service, monkeypatch):
    storage_error = RuntimeError("disk full")
    storage = _StubStorage(should_fail=storage_error)
    monkeypatch.setattr(uploads_local, "get_storage", lambda: storage)
    monkeypatch.setattr(uploads_local, "RabbitPublisher", lambda: _StubPublisher())

    db = _StubSession(store=service._test_store)  # type: ignore[attr-defined]
    called: dict = {}

    async def fake_mark_failed(self, video_id, reason):
        called["video_id"] = video_id
        called["reason"] = reason

    monkeypatch.setattr(LocalUploadService, "_mark_failed", fake_mark_failed, raising=False)

    with pytest.raises(RuntimeError) as exc:
        await service.upload(
            user_id="user-123",
            title="Gran jugada",
            upload_file=_make_file(),
            user_info={},
            db=db,
        )

    assert "disk full" in str(exc.value)
    assert storage.calls == []
    assert called["reason"] == "upload_failed"
    assert called["video_id"] == db.added.id  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_upload_service_mq_failure_reverts(service, monkeypatch):
    storage = _StubStorage()
    failing_pub = _StubPublisher(should_fail=RuntimeError("mq down"))
    monkeypatch.setattr(uploads_local, "get_storage", lambda: storage)
    monkeypatch.setattr(uploads_local, "RabbitPublisher", lambda: failing_pub)

    db = _StubSession(store=service._test_store)  # type: ignore[attr-defined]
    with pytest.raises(HTTPException) as exc:
        await service.upload(
            user_id="user-123",
            title="Gran jugada",
            upload_file=_make_file(),
            user_info={},
            db=db,
        )

    assert exc.value.status_code == 502
    assert "No se pudo encolar" in exc.value.detail
    video = db.added
    assert video.status is VideoStatus.uploaded
    assert video.correlation_id is None
    assert service._test_pipeline_session.rollback_calls == 1  # type: ignore[attr-defined]

@pytest.mark.asyncio
async def test_upload_service_bad_extension(service, monkeypatch):
    storage = _StubStorage()
    monkeypatch.setattr(uploads_local, "get_storage", lambda: storage)
    monkeypatch.setattr(uploads_local, "RabbitPublisher", lambda: _StubPublisher())

    db = _StubSession(store=service._test_store)  # type: ignore[attr-defined]
    bad_file = _make_file(name="clip.avi")

    with pytest.raises(HTTPException) as exc:
        await service.upload(
            user_id="user-123",
            title="Gran jugada",
            upload_file=bad_file,
            user_info={},
            db=db,
        )

    assert exc.value.status_code == 400
    assert "Formato no permitido" in exc.value.detail
    assert storage.calls == []


@pytest.mark.asyncio
async def test_upload_service_async_mode_schedules_pipeline(service_async, monkeypatch):
    calls: dict = {}

    def fake_schedule(self, **kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(LocalUploadService, "_schedule_background_pipeline", fake_schedule, raising=False)
    monkeypatch.setattr(uploads_local, "get_storage", lambda: _StubStorage())
    monkeypatch.setattr(uploads_local, "RabbitPublisher", lambda: _StubPublisher())

    db = _StubSession(store=service_async._test_store)  # type: ignore[attr-defined]
    await service_async.upload(
        user_id="user-123",
        title="Gran jugada",
        upload_file=_make_file(),
        user_info={},
        db=db,
    )

    assert "video_id" in calls and "filename" in calls
    assert calls["filename"].endswith(".mp4")


@pytest.mark.asyncio
async def test_process_pipeline_updates_video_and_removes_staging(monkeypatch, tmp_path):
    service = _build_service(monkeypatch, tmp_path, process_inline=True, storage_backend="s3")
    staging_file = tmp_path / "staged.bin"
    staging_file.write_bytes(b"payload")

    storage = _StubStorage()
    monkeypatch.setattr(uploads_local, "get_storage", lambda: storage)

    enqueued: dict = {}

    async def fake_enqueue(self, *, video, input_path, **kwargs):
        enqueued["video_id"] = str(video.id)
        enqueued["input_path"] = input_path

    monkeypatch.setattr(LocalUploadService, "_enqueue_processing", fake_enqueue, raising=False)

    pipeline_session = _StubSession(store={})
    video = type("VideoObj", (), {})()
    video.id = uuid.uuid4()
    video.original_path = "/staging/old"
    video.status = VideoStatus.uploaded
    video.correlation_id = "corr"
    pipeline_session.store[video.id] = video
    monkeypatch.setattr(uploads_local, "SessionLocal", lambda: _SessionCtx(pipeline_session))

    await service._process_pipeline(
        video_id=video.id,
        correlation_id="corr",
        staging_path=staging_file,
        filename="final.mp4",
        content_type="video/mp4",
        flush_duration_ms=1.2,
    )

    assert storage.calls[0][1] == "final.mp4"
    assert video.status is VideoStatus.processing
    assert enqueued["video_id"] == str(video.id)
    assert enqueued["input_path"].startswith("s3://tests-bucket/")
    assert not staging_file.exists()


@pytest.mark.asyncio
async def test_process_pipeline_upload_failure_marks_failed(monkeypatch, tmp_path):
    service = _build_service(monkeypatch, tmp_path, process_inline=True)
    staging_file = tmp_path / "staged.bin"
    staging_file.write_bytes(b"x")

    called: dict = {}

    async def fake_mark_failed(self, video_id, reason):
        called["video_id"] = video_id
        called["reason"] = reason

    async def fake_upload(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr(LocalUploadService, "_mark_failed", fake_mark_failed, raising=False)
    monkeypatch.setattr(LocalUploadService, "_upload_staged_file", fake_upload, raising=False)
    monkeypatch.setattr(uploads_local, "SessionLocal", lambda: _SessionCtx(_StubSession()))

    vid = uuid.uuid4()
    with pytest.raises(RuntimeError):
        await service._process_pipeline(
            video_id=vid,
            correlation_id="corr",
            staging_path=staging_file,
            filename="file.mp4",
            content_type="video/mp4",
            flush_duration_ms=0.5,
        )

    assert called["reason"] == "upload_failed"
    assert called["video_id"] == vid
    assert not staging_file.exists()


@pytest.mark.asyncio
async def test_stage_upload_file_uses_copy_when_source_exists(service, tmp_path):
    src = tmp_path / "source.mp4"
    src.write_bytes(b"video-data")
    upload_file = _DiskUploadFile(src)

    staged_path = await service._stage_upload_file(upload_file, "copy.mp4")
    upload_file.file.close()

    assert staged_path.exists()
    assert staged_path.read_bytes() == src.read_bytes()


@pytest.mark.asyncio
async def test_mark_failed_updates_video(monkeypatch, tmp_path):
    service = _build_service(monkeypatch, tmp_path, process_inline=True)
    session = _StubSession(store={})
    video = type("VideoObj", (), {})()
    video.id = uuid.uuid4()
    video.status = VideoStatus.processing
    video.correlation_id = "abc"
    session.store[video.id] = video
    monkeypatch.setattr(uploads_local, "SessionLocal", lambda: _SessionCtx(session))

    await service._mark_failed(video.id, "timeout")

    assert video.status is VideoStatus.failed
    assert video.correlation_id is None
    assert session.commits == 1

