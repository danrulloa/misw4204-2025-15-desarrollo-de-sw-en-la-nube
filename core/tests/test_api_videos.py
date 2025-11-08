# tests/test_api_videos.py
import io
import uuid

from fastapi import HTTPException, status

import app.api.videos as videos_mod


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

    class _StubVideoService:
        def __init__(self, *, list_result=None, get_result=None, delete_result=None,
                     get_exception: HTTPException | None = None,
                     delete_exception: HTTPException | None = None):
            self.list_result = list_result or []
            self.get_result = get_result
            self.delete_result = delete_result
            self.get_exception = get_exception
            self.delete_exception = delete_exception
            self.list_calls = []
            self.get_calls = []
            self.delete_calls = []

        async def list_user_videos(self, **kwargs):
            self.list_calls.append(kwargs)
            return self.list_result

        async def get_user_video(self, **kwargs):
            self.get_calls.append(kwargs)
            if self.get_exception:
                raise self.get_exception
            return self.get_result

        async def delete_user_video(self, **kwargs):
            self.delete_calls.append(kwargs)
            if self.delete_exception:
                raise self.delete_exception
            return self.delete_result

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
                "processed_path": "/processed/highlights.mp4",
            },
        )()

        stub_service = self._StubVideoService(list_result=[v])

        class _Sess:
            pass

        client.app.dependency_overrides[videos_mod.get_session] = lambda: _Sess()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.get("/api/videos", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list) and len(data) == 1
        assert data[0]["title"] == "Triple ganador"
        assert data[0]["status"] == "processed"
        # El backend puede retornar URL absoluta; comprobamos sufijo
        assert data[0]["processed_url"].endswith("/processed/highlights.mp4")

        assert len(stub_service.list_calls) == 1
        call = stub_service.list_calls[0]
        assert call["user_id"] == "test-user-1"
        assert call["limit"] == 20
        assert call["offset"] == 0

        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

    def test_get_video_detail_404(self, client, make_token):
        """GET detail: no existe -> 404."""
        stub_service = self._StubVideoService(
            get_exception=HTTPException(status_code=404, detail="Video no encontrado")
        )
        client.app.dependency_overrides[videos_mod.get_session] = lambda: object()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.get(
            "/api/videos/00000000-0000-0000-0000-000000000000",
            headers=self._auth(make_token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

    def test_get_video_detail_forbidden(self, client, make_token):
        """GET detail: el video no pertenece al usuario -> 403."""
        stub_service = self._StubVideoService(
            get_exception=HTTPException(status_code=403, detail="El video no pertenece al usuario")
        )
        client.app.dependency_overrides[videos_mod.get_session] = lambda: object()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.get("/api/videos/abc", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

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
                "original_path": "/uploads/original.mp4",
                "processed_path": "/processed/render.mp4",
            },
        )()

        stub_service = self._StubVideoService(get_result=vid)
        client.app.dependency_overrides[videos_mod.get_session] = lambda: object()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.get(f"/api/videos/{vid.id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["video_id"] == str(vid.id)
        assert data["title"] == "MVP"
        assert data["votes"] == 0
        # Comprobamos sufijos de URL en caso de ser absolutas
        assert data["original_url"].endswith("/uploads/original.mp4")
        assert data["processed_url"].endswith("/processed/render.mp4")
        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

    def test_delete_video_ya_procesado(self, client, make_token):
        """DELETE: status=processed -> 400."""
        error = HTTPException(status_code=400, detail="El video ya está listo para votación; no puede eliminarse.")
        stub_service = self._StubVideoService(delete_exception=error)
        client.app.dependency_overrides[videos_mod.get_session] = lambda: object()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.delete("/api/videos/abc", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

    def test_delete_video_ok(self, client, make_token):
        """DELETE: propio y no procesado -> 200."""
        video_id = "123"
        stub_service = self._StubVideoService(delete_result=video_id)
        client.app.dependency_overrides[videos_mod.get_session] = lambda: object()
        client.app.dependency_overrides[videos_mod.get_video_query_service] = lambda: stub_service

        resp = client.delete(f"/api/videos/{video_id}", headers=self._auth(make_token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["video_id"] == video_id
        assert stub_service.delete_calls

        client.app.dependency_overrides.pop(videos_mod.get_session, None)
        client.app.dependency_overrides.pop(videos_mod.get_video_query_service, None)

    def test_requires_auth_401(self, client):
        assert client.get("/api/videos").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.get("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
        assert client.delete("/api/videos/abc").status_code == status.HTTP_401_UNAUTHORIZED
