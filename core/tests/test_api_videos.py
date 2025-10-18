# tests/test_api_videos.py
import io
import uuid
import pytest
from fastapi import status

import app.api.videos as videos_mod


class TestVideoEndpoints:
    """Tests que realmente ejecutan la lógica de app/api/videos.py."""

    # ========= helpers comunes =========
    def _auth(self, make_token):
        return {"Authorization": f"Bearer {make_token(user_id='test-user-1')}"}

    class _DummyStorage:
        def save(self, fileobj, filename, content_type):
            # Simula que persistimos y devolvemos ruta relativa /uploads/...
            return f"/uploads/{filename}"

    class _DummyPublisher:
        def __init__(self):
            self.closed = False

        def publish_video(self, payload):  # no-op, pero valida que se pueda llamar
            assert "video_id" in payload and "input_path" in payload and "correlation_id" in payload

        def close(self):
            self.closed = True

    # ========= tests =========

    def test_upload_video_happy_path(self, client, monkeypatch, make_token):
        """POST /api/videos/upload: sube archivo válido -> 201 y cubre storage + Rabbit."""
        # parchea settings para formato y tamaño
        monkeypatch.setattr(videos_mod.settings, "ALLOWED_VIDEO_FORMATS", {"mp4"})
        monkeypatch.setattr(videos_mod.settings, "MAX_UPLOAD_SIZE_MB", 50)
        monkeypatch.setattr(videos_mod.settings, "WORKER_INPUT_PREFIX", "/worker/in")

        # parchea storage y publisher
        monkeypatch.setattr(videos_mod, "get_storage", lambda: self._DummyStorage())
        monkeypatch.setattr(videos_mod, "RabbitPublisher", self._DummyPublisher)

        # Fake AsyncSession con los métodos que usa upload_video
        class _UploadSession:
            def __init__(self):
                self._added = None
                self.committed = False
                self.refreshed = False

            def add(self, obj):
                self._added = obj

            async def commit(self):
                self.committed = True

            async def refresh(self, obj):
                # Asegura que haya un id para construir Location y la respuesta
                if getattr(obj, "id", None) is None:
                    obj.id = uuid.uuid4()
                self.refreshed = True

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _UploadSession()

        # arma archivo chico y válido
        file_bytes = b"\x00\x01video"
        files = {"video_file": ("jugada.mp4", io.BytesIO(file_bytes), "video/mp4")}
        data = {"title": "Mi video"}

        resp = client.post("/api/videos/upload", headers=self._auth(make_token), files=files, data=data)
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["message"].startswith("Video subido correctamente")
        assert "video_id" in body and "task_id" in body
        assert "Location" in resp.headers and resp.headers["Location"].startswith("/api/videos/")

        # limpia override
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_upload_video_rechaza_formato(self, client, monkeypatch, make_token):
        """Formato no permitido -> 400 (ejecuta _validate_ext_and_size)."""
        monkeypatch.setattr(videos_mod.settings, "ALLOWED_VIDEO_FORMATS", {"mp4"})  # solo mp4
        monkeypatch.setattr(videos_mod.settings, "MAX_UPLOAD_SIZE_MB", 50)
        # storage y publisher igual se parchean, pero no deberían usarse si falla antes
        monkeypatch.setattr(videos_mod, "get_storage", lambda: self._DummyStorage())
        monkeypatch.setattr(videos_mod, "RabbitPublisher", self._DummyPublisher)

        # sesión dummy por si acaso
        class _Sess:
            def add(self, o): ...
            async def commit(self): ...
            async def refresh(self, o): ...

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()

        files = {"video_file": ("clip.avi", io.BytesIO(b"xx"), "video/avi")}
        data = {"title": "tit"}
        resp = client.post("/api/videos/upload", headers=self._auth(make_token), files=files, data=data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_list_videos_ok(self, client, monkeypatch, make_token):
        """GET /api/videos: lista propia -> 200 y mapea schema."""
        # Fake fila "Video" mínima
        v = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "title": "Triple ganador",
                "status": "processed",
                "created_at": "2025-03-10T14:30:00Z",
                "processed_at": "2025-03-10T14:35:00Z",
            },
        )()

        class _Res:
            # simula result.scalars().all()
            def scalars(self):
                class _S:
                    def all(_): return [v]
                return _S()

        class _Sess:
            async def execute(self, stmt): return _Res()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()

        resp = client.get("/api/videos", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["title"] == "Triple ganador"
        assert data[0]["status"] == "processed"

        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_get_video_detail_404(self, client, make_token):
        """GET detail: no existe -> 404."""
        class _Sess:
            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_): return None
                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.get(
            "/api/videos/00000000-0000-0000-0000-000000000000",
            headers=self._auth(make_token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_get_video_detail_403(self, client, make_token):
        """GET detail: pertenece a otro usuario -> 403."""
        other_user_id = "someone-else"

        vid = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "user_id": other_user_id,
                "title": "Ajeno",
                "status": "uploaded",
                "created_at": "2025-03-10T14:30:00Z",
                "processed_at": None,
            },
        )()

        class _Sess:
            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_): return vid
                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.get(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_get_video_detail_ok(self, client, make_token):
        """GET detail: propio -> 200 y retorna schema completo."""
        uid = "test-user-1"
        vid = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "user_id": uid,
                "title": "MVP",
                "status": "processed",
                "created_at": "2025-03-10T14:30:00Z",
                "processed_at": "2025-03-10T14:35:00Z",
            },
        )()

        class _Sess:
            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_): return vid
                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.get(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["video_id"] == str(vid.id)
        assert data["title"] == "MVP"
        assert data["votes"] == 0  # el endpoint fija 0 por ahora
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_delete_video_ya_procesado(self, client, make_token):
        """DELETE: status=processed -> 400."""
        vid = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "user_id": "test-user-1",
                "status": "processed",
                "original_path": None,
                "processed_path": None,
            },
        )()

        class _Sess:
            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_): return vid
                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.delete(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_delete_video_ok(self, client, monkeypatch, make_token, tmp_path):
        """DELETE: propio y no procesado -> 200; cubre borrado físico y commit."""
        # Prepara rutas “reales” para cubrir _abs_storage_path y unlink
        upload_dir = tmp_path / "uploads"
        processed_dir = tmp_path / "processed"
        upload_dir.mkdir()
        processed_dir.mkdir()
        # ajusta settings
        monkeypatch.setattr(videos_mod.settings, "UPLOAD_DIR", str(upload_dir))
        monkeypatch.setattr(videos_mod.settings, "PROCESSED_DIR", str(processed_dir))

        # Crea archivos que el endpoint intentará borrar
        orig = upload_dir / "v1.mp4"
        proc = processed_dir / "v1.m3u8"
        orig.write_bytes(b"x")
        proc.write_bytes(b"y")

        vid = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "user_id": "test-user-1",
                "status": "uploaded",
                "original_path": "/uploads/v1.mp4",
                "processed_path": "/processed/v1.m3u8",
            },
        )()

        class _Sess:
            def __init__(self):
                self.deleted = None
                self.committed = False

            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_): return vid
                return _R()

            async def delete(self, obj):
                self.deleted = obj

            async def commit(self):
                self.committed = True

        sess = _Sess()
        client.app.dependency_overrides[videos_mod.get_session] = lambda: sess

        resp = client.delete(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["video_id"] == str(vid.id)
        assert not orig.exists() and not proc.exists()
        assert sess.deleted is vid and sess.committed is True

        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    # ====== sanity checks de auth 401 (mantén uno, no cuatro) ======
    def test_requires_auth_401(self, client):
        assert client.get("/api/videos").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.delete("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
