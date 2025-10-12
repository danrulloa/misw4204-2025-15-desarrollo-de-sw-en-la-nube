"""
Configuración de fixtures para pytest
"""

import pytest
import sys
from fastapi.testclient import TestClient
from main import app
from pathlib import Path


sys.path.append(str(Path(__file__).parent.parent))


@pytest.fixture
def client():
    """
    Fixture que proporciona un cliente de prueba para FastAPI
    """
    return TestClient(app)


@pytest.fixture
def valid_user_signup_data():
    """
    Fixture con datos válidos para registro de usuario
    """
    return {
        "first_name": "Pedro",
        "last_name": "Gomez",
        "email": "a@b.com",
        "password1": "123Qwweasd",
        "password2": "123Qwweasd",
        "city": "Bogotá",
        "country": "Colombia"
    }


@pytest.fixture
def valid_user_login_data():
    """
    Fixture con datos válidos para login
    """
    return {
        "email": "a@b.com",
        "password": "123Qwweasd"
    }


@pytest.fixture
def valid_video_data():
    """
    Fixture con datos válidos para video
    """
    return {
        "video_id": "abc123",
        "title": "Mi mejor tiro de 3",
        "status": "processed",
        "uploaded_at": "2025-03-10T14:30:00Z",
        "processed_at": "2025-03-10T14:35:00Z",
        "votes": 10
    }
