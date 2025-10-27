"""
Tests para funciones auxiliares de videos.py sin base de datos
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from fastapi import HTTPException, UploadFile, Request
from fastapi.security import HTTPAuthorizationCredentials
import jwt
import os
from pathlib import Path

from app.api.videos import _current_user_id, _validate_ext_and_size, _abs_storage_path, _get_user_from_request


class TestVideosFunctions:
    """Tests para funciones auxiliares de videos.py"""

    def test_current_user_id_valid_token(self):
        """Test que _current_user_id extrae sub correctamente"""
        mock_token = "valid.jwt.token"
        mock_payload = {"sub": "user123", "exp": 1234567890, "iat": 1234567800}
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {
                 'ACCESS_TOKEN_SECRET_KEY': 'test-secret',
                 'ALGORITHM': 'HS256',
                 'AUTH_AUDIENCE': 'anb-api',
                 'AUTH_ISSUER': 'anb-auth'
             }):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            result = _current_user_id(creds)
            
            assert result == "user123"
            mock_decode.assert_called_once_with(
                mock_token,
                'test-secret',
                algorithms=['HS256'],
                options={"require": ["exp", "iat"], "verify_aud": False, "verify_iss": False},
                audience='anb-api',
                issuer='anb-auth'
            )

    def test_current_user_id_no_sub(self):
        """Test que _current_user_id falla sin sub en payload"""
        mock_token = "valid.jwt.token"
        mock_payload = {"exp": 1234567890, "iat": 1234567800}  # Sin sub
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {
                 'ACCESS_TOKEN_SECRET_KEY': 'test-secret',
                 'ALGORITHM': 'HS256',
                 'AUTH_AUDIENCE': 'anb-api',
                 'AUTH_ISSUER': 'anb-auth'
             }):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_current_user_id_expired_token(self):
        """Test que _current_user_id maneja token expirado"""
        mock_token = "expired.jwt.token"
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {
                 'ACCESS_TOKEN_SECRET_KEY': 'test-secret',
                 'ALGORITHM': 'HS256',
                 'AUTH_AUDIENCE': 'anb-api',
                 'AUTH_ISSUER': 'anb-auth'
             }):
            
            mock_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token expirado" in exc_info.value.detail

    def test_current_user_id_invalid_token(self):
        """Test que _current_user_id maneja token inválido"""
        mock_token = "invalid.jwt.token"
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {
                 'ACCESS_TOKEN_SECRET_KEY': 'test-secret',
                 'ALGORITHM': 'HS256',
                 'AUTH_AUDIENCE': 'anb-api',
                 'AUTH_ISSUER': 'anb-auth'
             }):
            
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _current_user_id(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_validate_ext_and_size_valid_file(self):
        """Test que _validate_ext_and_size acepta archivo válido"""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file.tell.return_value = 1024 * 1024  # 1MB
        
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100
            
            ext, size = _validate_ext_and_size(mock_file)
            
            assert ext == "mp4"
            assert size == 1024 * 1024
            mock_file.file.seek.assert_called()

    def test_validate_ext_and_size_invalid_extension(self):
        """Test que _validate_ext_and_size rechaza extensión inválida"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test.txt"
        
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            
            with pytest.raises(HTTPException) as exc_info:
                _validate_ext_and_size(mock_file)
            
            assert exc_info.value.status_code == 400
            assert "Formato no permitido" in exc_info.value.detail

    def test_validate_ext_and_size_file_too_large(self):
        """Test que _validate_ext_and_size rechaza archivo muy grande"""
        mock_file = MagicMock()
        mock_file.filename = "test.mp4"
        mock_file.file.tell.return_value = 200 * 1024 * 1024  # 200MB
        
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100
            
            with pytest.raises(HTTPException) as exc_info:
                _validate_ext_and_size(mock_file)
            
            assert exc_info.value.status_code == 413
            assert "supera 100 MB" in exc_info.value.detail

    def test_validate_ext_and_size_no_filename(self):
        """Test que _validate_ext_and_size maneja archivo sin nombre"""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = None
        
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            
            with pytest.raises(HTTPException) as exc_info:
                _validate_ext_and_size(mock_file)
            
            assert exc_info.value.status_code == 400
            assert "Formato no permitido" in exc_info.value.detail

    def test_validate_ext_and_size_case_insensitive(self):
        """Test que _validate_ext_and_size es case insensitive"""
        mock_file = MagicMock()
        mock_file.filename = "test.MP4"  # Mayúsculas
        mock_file.file.tell.return_value = 1024 * 1024  # 1MB
        
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.ALLOWED_VIDEO_FORMATS = ["mp4", "avi", "mov"]
            mock_settings.MAX_UPLOAD_SIZE_MB = 100
            
            ext, size = _validate_ext_and_size(mock_file)
            
            assert ext == "mp4"  # Debe convertir a minúsculas

    def test_abs_storage_path_uploads(self):
        """Test que _abs_storage_path maneja rutas de uploads"""
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = "/app/uploads"
            
            result = _abs_storage_path("/uploads/video.mp4")
            assert result == Path("/app/uploads/video.mp4")

    def test_abs_storage_path_processed(self):
        """Test que _abs_storage_path maneja rutas de processed"""
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.PROCESSED_DIR = "/app/processed"
            
            result = _abs_storage_path("/processed/video.mp4")
            assert result == Path("/app/processed/video.mp4")

    def test_abs_storage_path_relative(self):
        """Test que _abs_storage_path maneja rutas relativas"""
        with patch('app.api.videos.settings') as mock_settings:
            mock_settings.UPLOAD_DIR = "/app/uploads"
            
            result = _abs_storage_path("video.mp4")
            assert result == Path("/app/uploads/video.mp4")

    def test_abs_storage_path_empty(self):
        """Test que _abs_storage_path maneja ruta vacía"""
        result = _abs_storage_path("")
        assert result == Path("/non/existent")

    def test_abs_storage_path_none(self):
        """Test que _abs_storage_path maneja ruta None"""
        result = _abs_storage_path(None)
        assert result == Path("/non/existent")

    def test_get_user_from_request(self):
        """Test que _get_user_from_request extrae información del usuario"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user = {
            "user_id": "12345",
            "first_name": "John",
            "last_name": "Doe",
            "city": "Bogotá"
        }
        
        result = _get_user_from_request(mock_request)
        
        assert result["user_id"] == "12345"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        assert result["city"] == "Bogotá"

    def test_get_user_from_request_missing_fields(self):
        """Test que _get_user_from_request maneja campos faltantes"""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user = {
            "user_id": "12345"
            # Faltan otros campos
        }
        
        result = _get_user_from_request(mock_request)
        
        assert result["user_id"] == "12345"
        assert result["first_name"] == ""
        assert result["last_name"] == ""
        assert result["city"] == ""
