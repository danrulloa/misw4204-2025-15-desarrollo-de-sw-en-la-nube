"""Tests unitarios para LocalUploadService."""

import io
import uuid

import pytest
from fastapi import HTTPException, UploadFile

from app.models.video import VideoStatus
from app.services.uploads import local as uploads_local
from app.services.uploads.local import LocalUploadService


class _StubSession:
    def __init__(self):
        self.added = None
        self.commits = 0
        self.refresh_calls = 0
        self.flush_calls = 0
        self.rollback_calls = 0

    def add(self, obj):
        self.added = obj

    async def commit(self):
        self.commits += 1

    async def flush(self):
        self.flush_calls += 1
        # Simular asignación de ID en flush (similar a refresh)
        if getattr(self.added, "id", None) is None:
            self.added.id = uuid.uuid4()

    async def rollback(self):
        self.rollback_calls += 1

    async def refresh(self, obj):
        self.refresh_calls += 1
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()


class _StubStorage:
    def __init__(self, *, should_fail: Exception | None = None):
        self.should_fail = should_fail
        self.calls = []

    def save(self, fileobj, filename, content_type):
        if self.should_fail:
            raise self.should_fail
        self.calls.append(("save", filename, content_type))
        return f"/uploads/{filename}"

    def save_with_key(self, fileobj, key, content_type):
        if self.should_fail:
            raise self.should_fail
        self.calls.append(("save_with_key", key, content_type))
        return f"/{key}"


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


def _make_file(name: str = "clip.mp4", data: bytes = b"video") -> UploadFile:
    return _FakeUploadFile(name, data, "video/mp4")  # type: ignore[return-value]


class _ImmediateBackgroundTasks:
    """Stub de BackgroundTasks que ejecuta inmediatamente la tarea agregada."""

    def add_task(self, func, *args, **kwargs):
        return func(*args, **kwargs)


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(uploads_local.settings, "ALLOWED_VIDEO_FORMATS", {"mp4"})
    monkeypatch.setattr(uploads_local.settings, "MAX_UPLOAD_SIZE_MB", 100)
    # S3 config de pruebas (no se usa realmente porque se parchea STORAGE)
    monkeypatch.setattr(uploads_local.settings, "S3_BUCKET", "test-bucket")
    monkeypatch.setattr(uploads_local.settings, "S3_PREFIX", "uploads")
    return LocalUploadService()


@pytest.mark.asyncio
async def test_upload_service_happy_path(service, monkeypatch):
    storage = _StubStorage()
    publisher = _StubPublisher()
    # Parchea el STORAGE fijo del módulo a nuestro stub
    monkeypatch.setattr(uploads_local, "STORAGE", storage)
    monkeypatch.setattr(uploads_local, "QueuePublisher", lambda: publisher)

    db = _StubSession()
    user_info = {"first_name": "Ana", "last_name": "Player", "city": "Bogota"}

    video, correlation = await service.upload(
        user_id="user-123",
        title="Gran jugada",
        upload_file=_make_file(),
        user_info=user_info,
        db=db,
        correlation_id="test-corr-1",
        background_tasks=_ImmediateBackgroundTasks(),
    )

    assert len(storage.calls) == 1
    method, saved_name, saved_type = storage.calls[0]
    assert method == "save_with_key"
    assert saved_name.endswith(".mp4")
    assert saved_type == "video/mp4"

    assert db.added is video
    assert db.commits == 1  # Commit temprano
    assert db.flush_calls == 1  # Flush para obtener ID
    assert db.refresh_calls == 0  # Ya no necesitamos refresh
    assert video.status is VideoStatus.uploaded
    assert video.correlation_id == correlation
    assert video.player_first_name == "Ana"

    assert publisher.payload == {
        "video_id": str(video.id),
        "input_path": f"s3://{uploads_local.settings.S3_BUCKET}/{video.original_path.lstrip('/')}",
        "correlation_id": correlation,
    }
    assert publisher.closed is True


@pytest.mark.asyncio
async def test_upload_service_storage_failure(service, monkeypatch):
    storage_error = RuntimeError("disk full")
    storage = _StubStorage(should_fail=storage_error)
    monkeypatch.setattr(uploads_local, "STORAGE", storage)
    monkeypatch.setattr(uploads_local, "QueuePublisher", lambda: _StubPublisher())

    db = _StubSession()
    # Con pipeline en background, el error ocurre en la tarea y no hay llamada a save_with_key; no se propaga.
    video, correlation = await service.upload(
        user_id="user-123",
        title="Gran jugada",
        upload_file=_make_file(),
        user_info={},
        db=db,
        correlation_id="test-corr-2",
        background_tasks=_ImmediateBackgroundTasks(),
    )

    # La llamada retorna sin subir (falló en pipeline inmediatamente). No hubo save_with_key exitoso.
    # El stub no registra llamadas cuando falla, por eso queda en 0.
    assert len(storage.calls) == 0
    assert db.added is not None
    assert db.commits == 1


@pytest.mark.asyncio
async def test_upload_service_mq_failure_reverts(service, monkeypatch):
    storage = _StubStorage()
    failing_pub = _StubPublisher(should_fail=RuntimeError("mq down"))
    monkeypatch.setattr(uploads_local, "STORAGE", storage)
    monkeypatch.setattr(uploads_local, "QueuePublisher", lambda: failing_pub)

    db = _StubSession()
    # El fallo de MQ ocurre en el pipeline; la llamada principal retorna 200
    video, correlation = await service.upload(
        user_id="user-123",
        title="Gran jugada",
        upload_file=_make_file(),
        user_info={},
        db=db,
        correlation_id="test-corr-3",
        background_tasks=_ImmediateBackgroundTasks(),
    )

    assert len(storage.calls) == 1
    assert db.added is not None
    assert db.commits == 1


@pytest.mark.asyncio
async def test_upload_service_bad_extension(service, monkeypatch):
    storage = _StubStorage()
    monkeypatch.setattr(uploads_local, "STORAGE", storage)
    monkeypatch.setattr(uploads_local, "QueuePublisher", lambda: _StubPublisher())

    db = _StubSession()
    bad_file = _make_file(name="clip.avi")

    with pytest.raises(HTTPException) as exc:
        await service.upload(
            user_id="user-123",
            title="Gran jugada",
            upload_file=bad_file,
            user_info={},
            db=db,
            correlation_id="test-corr-4",
        )

    assert exc.value.status_code == 400
    assert "Formato no permitido" in exc.value.detail
    assert storage.calls == []