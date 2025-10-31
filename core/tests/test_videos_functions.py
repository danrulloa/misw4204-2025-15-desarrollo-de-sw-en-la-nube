"""
Tests para funciones auxiliares de videos.py sin base de datos
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import jwt
import pytest
from fastapi import HTTPException, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials

from app.api.videos import _current_user_id, _get_user_from_request
from app.services.storage.utils import abs_storage_path
from app.services.uploads.local import LocalUploadService


class TestVideosFunctions:
    """Tests para funciones auxiliares de videos.py"""

    def test_current_user_id_valid_token(self):
        """_current_user_id extrae el sub de un token válido"""
        mock_token = "valid.jwt.token"
        mock_payload = {"sub": "user123", "exp": 1234567890, "iat": 1234567800}

        with patch("jwt.decode") as mock_decode, patch.dict(
            os.environ,
            {
                "ACCESS_TOKEN_SECRET_KEY": "test-secret",
                "ALGORITHM": "HS256",
                "AUTH_AUDIENCE": "anb-api",
                "AUTH_ISSUER": "anb-auth",
            },
        ):
            mock_decode.return_value = mock_payload

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            result = _current_user_id(creds)

            assert result == "user123"
            mock_decode.assert_called_once_with(
                mock_token,
                "test-secret",
                algorithms=["HS256"],
                options={"require": ["exp", "iat"], "verify_aud": False, "verify_iss": False},
                audience="anb-api",
                issuer="anb-auth",
            )

    def test_current_user_id_no_sub(self):
        """_current_user_id falla cuando el payload no trae sub"""
        mock_token = "valid.jwt.token"
        mock_payload = {"exp": 1234567890, "iat": 1234567800}

        with patch("jwt.decode") as mock_decode, patch.dict(
            os.environ,
            {
                "ACCESS_TOKEN_SECRET_KEY": "test-secret",
                "ALGORITHM": "HS256",
                "AUTH_AUDIENCE": "anb-api",
                "AUTH_ISSUER": "anb-auth",
            },
        ):
            mock_decode.return_value = mock_payload

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)

            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)

            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_current_user_id_expired_token(self):
        """_current_user_id propaga expiración de token"""
        mock_token = "expired.jwt.token"

        with patch("jwt.decode") as mock_decode, patch.dict(
            os.environ,
            {
                "ACCESS_TOKEN_SECRET_KEY": "test-secret",
                "ALGORITHM": "HS256",
                "AUTH_AUDIENCE": "anb-api",
                "AUTH_ISSUER": "anb-auth",
            },
        ):
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)

            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)

            assert exc_info.value.status_code == 401
            assert "Token expirado" in exc_info.value.detail

    def test_current_user_id_invalid_token(self):
        """_current_user_id retorna 401 si el token es inválido"""
        mock_token = "invalid.jwt.token"

        with patch("jwt.decode") as mock_decode, patch.dict(
            os.environ,
            {
                "ACCESS_TOKEN_SECRET_KEY": "test-secret",
                "ALGORITHM": "HS256",
                "AUTH_AUDIENCE": "anb-api",
                "AUTH_ISSUER": "anb-auth",
            },
        ):
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)

            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)

            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_validate_ext_and_size_valid_file(self):
        """LocalUploadService._validate_ext_and_size acepta archivo permitido"""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file.tell.return_value = 1024 * 1024

        with patch("app.services.uploads.local.settings") as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100

            service = LocalUploadService()
            ext, size = service._validate_ext_and_size(mock_file)

            assert ext == "mp4"
            assert size == 1024 * 1024
            mock_file.file.seek.assert_called()

    def test_validate_ext_and_size_invalid_extension(self):
        """LocalUploadService._validate_ext_and_size rechaza extensión desconocida"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"

        with patch("app.services.uploads.local.settings") as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]

            with pytest.raises(HTTPException) as exc_info:
                LocalUploadService()._validate_ext_and_size(mock_file)

            assert exc_info.value.status_code == 400
            assert "Formato no permitido" in exc_info.value.detail

    def test_validate_ext_and_size_file_too_large(self):
        """LocalUploadService._validate_ext_and_size rechaza archivo grande"""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file.tell.return_value = 200 * 1024 * 1024

        with patch("app.services.uploads.local.settings") as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100

            with pytest.raises(HTTPException) as exc_info:
                LocalUploadService()._validate_ext_and_size(mock_file)

            assert exc_info.value.status_code == 413
            assert "supera 100 MB" in exc_info.value.detail

    def test_validate_ext_and_size_no_filename(self):
        """LocalUploadService._validate_ext_and_size exige nombre de archivo"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None

        with patch("app.services.uploads.local.settings") as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]

            with pytest.raises(HTTPException) as exc_info:
                LocalUploadService()._validate_ext_and_size(mock_file)

            assert exc_info.value.status_code == 400
            assert "Formato no permitido" in exc_info.value.detail

    def test_validate_ext_and_size_case_insensitive(self):
        """LocalUploadService._validate_ext_and_size ignora mayúsculas"""
        mock_file = MagicMock()
        mock_file.filename = "test.MP4"
        mock_file.file.tell.return_value = 1024 * 1024

        with patch("app.services.uploads.local.settings") as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100

            ext, _ = LocalUploadService()._validate_ext_and_size(mock_file)

            assert ext == "mp4"

    def test_abs_storage_path_uploads(self):
        """abs_storage_path arma ruta absoluta para uploads"""
        with patch("app.services.storage.utils.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = "/app/uploads"

            result = abs_storage_path("/uploads/video.mp4")
            assert result == Path("/app/uploads/video.mp4")

    def test_abs_storage_path_processed(self):
        """abs_storage_path arma ruta absoluta para processed"""
        with patch("app.services.storage.utils.settings") as mock_settings:
            mock_settings.PROCESSED_DIR = "/app/processed"

            result = abs_storage_path("/processed/video.mp4")
            assert result == Path("/app/processed/video.mp4")

    def test_abs_storage_path_relative(self):
        """abs_storage_path usa UPLOAD_DIR para rutas relativas"""
        with patch("app.services.storage.utils.settings") as mock_settings:
            mock_settings.UPLOAD_DIR = "/app/uploads"

            result = abs_storage_path("video.mp4")
            assert result == Path("/app/uploads/video.mp4")

    def test_abs_storage_path_empty(self):
        """abs_storage_path devuelve ruta dummy cuando está vacío"""
        result = abs_storage_path("")
        assert result == Path("/non/existent")

    def test_abs_storage_path_none(self):
        """abs_storage_path maneja valores None"""
        result = abs_storage_path(None)
        assert result == Path("/non/existent")

    def test_get_user_from_request(self):
        """_get_user_from_request retorna campos esperados"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user = {
            "user_id": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "city": "Bogotá",
        }

        result = _get_user_from_request(mock_request)

        assert result["user_id"] == "12345"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["city"] == "Bogotá"

    def test_get_user_from_request_missing_fields(self):
        """_get_user_from_request completa campos faltantes con vacío"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user = {"user_id": "12345"}

        result = _get_user_from_request(mock_request)

        assert result["user_id"] == "12345"
        assert result["first_name"] == ""
        assert result["last_name"] == ""
        assert result["city"] == ""
