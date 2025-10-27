"""
Tests para el middleware de autenticación
Valida exclusiones, rutas públicas, 401 y propagación de usuario
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from jose import JWTError
from tests.conftest import make_token


class TestAuthMiddlewareExclusions:
    """Tests para rutas excluidas del middleware"""
    
    def test_root_endpoint_no_auth(self, client):
        """Root no requiere autenticación"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_health_endpoint_no_auth(self, client):
        """Health check no requiere autenticación"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_docs_endpoint_no_auth(self, client):
        """Swagger docs no requiere autenticación"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json_no_auth(self, client):
        """OpenAPI spec no requiere autenticación"""
        response = client.get("/openapi.json")
        assert response.status_code == 200




class TestAuthMiddlewareProtectedRoutes:
    """Tests para rutas protegidas que requieren autenticación"""
    
    def test_videos_endpoint_requires_auth(self, client):
        """GET /api/videos requiere Authorization header"""
        response = client.get("/api/videos")
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_videos_detail_requires_auth(self, client):
        """GET /api/videos/{id} requiere Authorization header"""
        response = client.get("/api/videos/abc123")
        assert response.status_code == 401
    
    def test_video_delete_requires_auth(self, client):
        """DELETE /api/videos/{id} requiere Authorization header"""
        response = client.delete("/api/videos/abc123")
        assert response.status_code == 401


class TestAuthMiddlewareTokenValidation:
    """Tests para validación de tokens JWT"""
    
    def test_missing_authorization_header(self, client):
        """Sin header Authorization retorna 401"""
        response = client.get("/api/videos")
        assert response.status_code == 401
        data = response.json()
        assert "Missing or invalid Authorization header" in data["detail"]
    
    def test_invalid_authorization_format(self, client):
        """Header sin formato 'Bearer ' retorna 401"""
        response = client.get("/api/videos", headers={"Authorization": "InvalidFormat token123"})
        assert response.status_code == 401
        data = response.json()
        assert "Missing or invalid Authorization header" in data["detail"]
    
    @patch("app.core.auth_middleware.jwt.decode")
    def test_invalid_token_signature(self, mock_decode, client):
        """Token con firma inválida retorna 401"""
        mock_decode.side_effect = JWTError("Invalid signature")
        
        response = client.get("/api/videos", headers={"Authorization": "Bearer invalid-token"})
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]
    
    @patch("app.core.auth_middleware.jwt.decode")
    def test_expired_token(self, mock_decode, client):
        """Token expirado retorna 401"""
        mock_decode.side_effect = JWTError("Signature has expired")
        
        response = client.get("/api/videos", headers={"Authorization": "Bearer expired-token"})
        assert response.status_code == 401
        data = response.json()
        assert "Invalid or expired token" in data["detail"]



