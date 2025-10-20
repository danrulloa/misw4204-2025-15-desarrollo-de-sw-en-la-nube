"""
Tests para endpoints de la API
"""

import pytest
from fastapi import status


class TestRootEndpoints:
    """Tests para endpoints raíz"""
    
    def test_root_endpoint(self, client):
        """Test endpoint raíz"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Tests para endpoints de autenticación"""
    
    def test_signup_endpoint_exists(self, client):
        """Test que el endpoint de signup existe"""
        response = client.post("/api/auth/signup", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
            "city": "Bogotá",
            "country": "Colombia"
        })
        # Debe retornar 501 (Not Implemented) por ahora
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_login_endpoint_exists(self, client):
        """Test que el endpoint de login existe"""
        response = client.post("/api/auth/login", json={
            "email": "john@example.com",
            "password": "SecurePass123"
        })
        # Debe retornar 501 (Not Implemented) por ahora
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_signup_validation_error(self, client):
        """Test validación en signup"""
        response = client.post("/api/auth/signup", json={
            "first_name": "John"
            # Faltan campos requeridos
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data


class TestVideoEndpoints:
    """Tests para endpoints de videos (según api/videos.py).
    Todos requieren autenticación; sin token deben responder 401.
    """

    def test_upload_video_endpoint_requires_auth(self, client):
        # POST /api/videos/upload sin Authorization → 401
        resp = client.post("/api/videos/upload")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_videos_endpoint_requires_auth(self, client):
        # GET /api/videos sin Authorization → 401
        resp = client.get("/api/videos")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_video_detail_endpoint_requires_auth(self, client):
        # GET /api/videos/{video_id} sin Authorization → 401
        resp = client.get("/api/videos/abc123")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_video_endpoint_requires_auth(self, client):
        # DELETE /api/videos/{video_id} sin Authorization → 401
        resp = client.delete("/api/videos/abc123")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


class TestPublicEndpoints:
    """Tests para endpoints públicos"""
    
    def test_list_public_videos_endpoint_exists(self, client):
        """Test que el endpoint de videos públicos existe"""
        response = client.get("/api/public/videos")
        # Debe retornar 501 (Not Implemented) por ahora
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_vote_endpoint_exists(self, client):
        """Test que el endpoint de votar existe"""
        response = client.post("/api/public/videos/abc123/vote")
        # Debe retornar 501 (Not Implemented) por ahora
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_rankings_endpoint_exists(self, client):
        """Test que el endpoint de rankings existe"""
        response = client.get("/api/public/rankings")
        # Debe retornar 501 (Not Implemented) por ahora
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_rankings_with_city_filter(self, client):
        """Test rankings con filtro de ciudad"""
        response = client.get("/api/public/rankings?city=Bogotá")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    
    def test_rankings_with_limit(self, client):
        """Test rankings con límite"""
        response = client.get("/api/public/rankings?limit=5")
        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


class TestOpenAPIDocumentation:
    """Tests para documentación OpenAPI"""
    
    def test_openapi_json_available(self, client):
        """Test que la especificación OpenAPI está disponible"""
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
    
    def test_swagger_ui_available(self, client):
        """Test que Swagger UI está disponible"""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
    
    def test_redoc_available(self, client):
        """Test que ReDoc está disponible"""
        response = client.get("/redoc")
        assert response.status_code == status.HTTP_200_OK
