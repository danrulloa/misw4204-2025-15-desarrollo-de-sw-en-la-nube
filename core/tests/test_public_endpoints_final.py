"""
Tests para endpoints públicos - Sin base de datos
Estos tests validan la lógica sin depender de infraestructura externa
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from main import app


class TestPublicEndpoints:
    """Tests para endpoints públicos"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_vote_endpoint_requires_auth(self, client):
        """Test que el endpoint de votar requiere autenticación"""
        response = client.post("/api/public/videos/abc123/vote")
        
        # Debe retornar 401 (Unauthorized) porque requiere token
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data
    
    def test_vote_endpoint_with_invalid_token(self, client):
        """Test que el endpoint rechaza tokens inválidos"""
        response = client.post(
            "/api/public/videos/abc123/vote",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert "detail" in data
    
    def test_rankings_invalid_limit(self, client):
        """Test que rankings rechaza límites inválidos"""
        response = client.get("/api/public/rankings?limit=0")
        
        # La aplicación retorna 400 (Bad Request) por límite inválido
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_rankings_invalid_limit_too_high(self, client):
        """Test que rankings rechaza límites muy altos"""
        response = client.get("/api/public/rankings?limit=1000")
        
        # La aplicación retorna 400 (Bad Request) por límite muy alto
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_videos_invalid_limit(self, client):
        """Test que videos rechaza límites inválidos"""
        response = client.get("/api/public/videos?limit=0")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_videos_invalid_offset(self, client):
        """Test que videos rechaza offsets inválidos"""
        response = client.get("/api/public/videos?offset=-1")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPublicEndpointsValidation:
    """Tests de validación para endpoints públicos"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_query_parameters_validation(self, client):
        """Test validación de parámetros de query"""
        # Parámetros inválidos
        response = client.get("/api/public/videos?limit=abc")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        response = client.get("/api/public/rankings?limit=xyz")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestPublicEndpointsAuth:
    """Tests de autenticación para endpoints públicos"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_public_vote_requires_auth(self, client):
        """POST /api/public/videos/{id}/vote requiere autenticación"""
        response = client.post("/api/public/videos/abc123/vote")
        # Debe ser 401 (requiere auth)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestPublicEndpointsStructure:
    """Tests de estructura para endpoints públicos"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_openapi_docs_exist(self, client):
        """Test que la documentación OpenAPI existe"""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK
        
        response = client.get("/openapi.json")
        assert response.status_code == status.HTTP_200_OK
    
    def test_health_check_exists(self, client):
        """Test que el health check existe"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
    
    def test_root_endpoint_exists(self, client):
        """Test que el endpoint raíz existe"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK


