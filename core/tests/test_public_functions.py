"""
Tests para funciones específicas de public.py sin base de datos
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
import jwt
import os

from app.api.public import _get_user_id_from_token


class TestPublicFunctions:
    """Tests para funciones auxiliares de public.py"""

    def test_get_user_id_from_token_valid(self):
        """Test que _get_user_id_from_token extrae user_id correctamente"""
        # Mock del token JWT válido
        mock_token = "valid.jwt.token"
        mock_payload = {"user_id": "12345", "exp": 1234567890}
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            result = _get_user_id_from_token(creds)
            
            assert result == "12345"
            mock_decode.assert_called_once_with(
                mock_token,
                'test-secret',
                algorithms=['HS256']
            )

    def test_get_user_id_from_token_no_creds(self):
        """Test que _get_user_id_from_token falla sin credenciales"""
        with pytest.raises(HTTPException) as exc_info:
            _get_user_id_from_token(None)
        
        assert exc_info.value.status_code == 401
        assert "Se requiere autenticación" in exc_info.value.detail

    def test_get_user_id_from_token_invalid_jwt(self):
        """Test que _get_user_id_from_token maneja JWT inválido"""
        mock_token = "invalid.jwt.token"
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _get_user_id_from_token(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_get_user_id_from_token_no_user_id(self):
        """Test que _get_user_id_from_token falla sin user_id en payload"""
        mock_token = "valid.jwt.token"
        mock_payload = {"exp": 1234567890}  # Sin user_id
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _get_user_id_from_token(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_get_user_id_from_token_empty_user_id(self):
        """Test que _get_user_id_from_token falla con user_id vacío"""
        mock_token = "valid.jwt.token"
        mock_payload = {"user_id": "", "exp": 1234567890}
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _get_user_id_from_token(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_get_user_id_from_token_none_user_id(self):
        """Test que _get_user_id_from_token falla con user_id None"""
        mock_token = "valid.jwt.token"
        mock_payload = {"user_id": None, "exp": 1234567890}
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            
            with pytest.raises(HTTPException) as exc_info:
                _get_user_id_from_token(creds)
            
            assert exc_info.value.status_code == 401
            assert "Token inválido" in exc_info.value.detail

    def test_get_user_id_from_token_converts_to_string(self):
        """Test que _get_user_id_from_token convierte user_id a string"""
        mock_token = "valid.jwt.token"
        mock_payload = {"user_id": 12345, "exp": 1234567890}  # user_id como int
        
        with patch('jwt.decode') as mock_decode, \
             patch.dict(os.environ, {'ACCESS_TOKEN_SECRET_KEY': 'test-secret', 'ALGORITHM': 'HS256'}):
            
            mock_decode.return_value = mock_payload
            
            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=mock_token)
            result = _get_user_id_from_token(creds)
            
            assert result == "12345"
            assert isinstance(result, str)
