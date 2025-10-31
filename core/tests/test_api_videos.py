# tests/test_api_videos.py
import io
import uuid

from fastapi import HTTPException, status

import app.api.videos as videos_mod
import app.services.storage.utils as storage_utils


class TestVideoEndpoints:
    """Tests que ejercitan app/api/videos.py."""

    def _auth(self, make_token):
        return {"Authorization": f"Bearer {make_token(user_id='test-user-1')}"}

    class _StubUploadService:
        def __init__(self):
            self.calls = []
            self.should_raise: HTTPException | None = None

        async def upload(self, **kwargs):
            self.calls.append(kwargs)
            if self.should_raise:
                raise self.should_raise
            fake_video = type("Video", (), {"id": uuid.uuid4()})()
            return fake_video, "task-123"

    def test_upload_video_happy_path(self, client, monkeypatch, make_token):
        """POST /api/videos/upload delega en el servicio y responde 201."""
        stub_service = self._StubUploadService()
        monkeypatch.setattr(videos_mod, "get_upload_service", lambda: stub_service)

        class _Sess:
            pass

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()

        files = {"video_file": ("jugada.mp4", io.BytesIO(b"data"), "video/mp4")}
        data = {"title": "Mi video"}

        resp = client.post("/api/videos/upload", headers=self._auth(make_token), files=files, data=data)
        assert resp.status_code == status.HTTP_201_CREATED
        body = resp.json()
        assert body["message"].startswith("Video subido correctamente")
        assert body["video_id"]
        assert body["task_id"] == "task-123"
        assert resp.headers["Location"].startswith("/api/videos/")

        assert len(stub_service.calls) == 1
        call = stub_service.calls[0]
        assert call["user_id"] == "test-user-1"
        assert call["title"] == "Mi video"
        assert "user_id" in call["user_info"]

        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_upload_video_rechaza_formato(self, client, monkeypatch, make_token):
        """Si el servicio lanza HTTPException debe propagarse."""
        stub_service = self._StubUploadService()
        stub_service.should_raise = HTTPException(status_code=400, detail="Formato no permitido")
        monkeypatch.setattr(videos_mod, "get_upload_service", lambda: stub_service)

        class _Sess:
            pass

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()

        files = {"video_file": ("clip.avi", io.BytesIO(b"xx"), "video/avi")}
        data = {"title": "tit"}
        resp = client.post("/api/videos/upload", headers=self._auth(make_token), files=files, data=data)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert resp.json()["detail"] == "Formato no permitido"
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_list_videos_ok(self, client, monkeypatch, make_token):
        """GET /api/videos: lista propia -> 200 y mapea schema."""
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
            def scalars(self):
                class _S:
                    def all(_):
                        return [v]

                return _S()

        class _Sess:
            async def execute(self, stmt):
                return _Res()

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
                    def scalar_one_or_none(_):
                        return None

                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.get("/api/videos/00000000-0000-0000-0000-000000000000", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_get_video_detail_forbidden(self, client, make_token):
        """GET detail: el video no pertenece al usuario -> 403."""
        vid = type(
            "V",
            (),
            {
                "id": uuid.uuid4(),
                "user_id": "other-user",
                "title": "No mío",
                "status": "uploaded",
                "created_at": "2025-01-01T00:00:00Z",
                "processed_at": None,
            },
        )()

        class _Sess:
            async def execute(self, stmt):
                class _R:
                    def scalar_one_or_none(_):
                        return vid

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
                    def scalar_one_or_none(_):
                        return vid

                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.get(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["video_id"] == str(vid.id)
        assert data["title"] == "MVP"
        assert data["votes"] == 0
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
                    def scalar_one_or_none(_):
                        return vid

                return _R()

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        resp = client.delete(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        client.app.dependency_overrides.pop(videos_mod.get_session, None)

    def test_delete_video_ok(self, client, monkeypatch, make_token, tmp_path):
        """DELETE: propio y no procesado -> 200; borra archivos."""
        upload_dir = tmp_path / "uploads"
        processed_dir = tmp_path / "processed"
        upload_dir.mkdir()
        processed_dir.mkdir()
        monkeypatch.setattr(storage_utils.settings, "UPLOAD_DIR", str(upload_dir))
        monkeypatch.setattr(storage_utils.settings, "PROCESSED_DIR", str(processed_dir))

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
                    def scalar_one_or_none(_):
                        return vid

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

    def test_requires_auth_401(self, client):
        assert client.get("/api/videos").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.delete("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
