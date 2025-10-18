"""
Configuración de fixtures para pytest
"""

import pytest
import sys
import os
import time
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


@pytest.fixture(autouse=True)
def patch_env(monkeypatch):
    """
    Configura variables de entorno necesarias para JWT
    """
    monkeypatch.setenv("ACCESS_TOKEN_SECRET_KEY", "test-secret-key-12345")
    monkeypatch.setenv("ALGORITHM", "HS256")


def make_token(user_id="test-user-1", **extra_claims):
    """
    Helper para crear tokens JWT de prueba
    """
    import jwt
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "sub": user_id,
        "iat": now,
        "exp": now + 3600,
        "first_name": extra_claims.get("first_name", "Test"),
        "last_name": extra_claims.get("last_name", "User"),
        "city": extra_claims.get("city", "Bogotá"),
        **extra_claims
    }
    return jwt.encode(
        payload,
        os.getenv("ACCESS_TOKEN_SECRET_KEY", "test-secret-key-12345"),
        algorithm=os.getenv("ALGORITHM", "HS256")
    )


def fake_row(**attrs):
    """
    Crea un objeto con atributos dinámicos para simular filas de BD
    """
    class FakeRow:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    return FakeRow(**attrs)


class FakeResult:
    """
    Simula el resultado de una query SQLAlchemy
    """
    def __init__(self, all_items=None, one=None, scalar=None):
        self._all = all_items if all_items is not None else []
        self._one = one
        self._scalar = scalar
    
    def all(self):
        return self._all
    
    def one_or_none(self):
        return self._one
    
    def scalar_one_or_none(self):
        return self._scalar


class FakeAsyncSession:
    """
    Simula una AsyncSession de SQLAlchemy con comportamiento controlado
    """
    def __init__(self, results=None):
        """
        results puede ser:
        - Una lista de FakeResult (se consume en orden)
        - Un dict con clave por etapa
        - Un FakeResult único
        """
        self.results = results or []
        self.committed = False
        self.rolled_back = False
        self.call_count = 0
    
    async def execute(self, stmt):
        self.call_count += 1
        if isinstance(self.results, list):
            return self.results.pop(0) if self.results else FakeResult()
        elif isinstance(self.results, dict):
            key = f"call_{self.call_count}"
            return self.results.get(key, self.results.get("default", FakeResult()))
        else:
            return self.results
    
    async def commit(self):
        self.committed = True
    
    async def rollback(self):
        self.rolled_back = True
    
    def add(self, obj):
        pass


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
