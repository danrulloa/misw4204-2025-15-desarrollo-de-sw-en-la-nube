# tests/conftest.py
"""
Configuración de fixtures para pytest
"""
import os
import sys
import time
import types
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from jose import jwt


if "prometheus_fastapi_instrumentator" not in sys.modules:
    class _StubInstrumentator:
        def __init__(self, *args, **kwargs):
            pass

        def instrument(self, app):
            return self

        def expose(self, app, endpoint="/metrics", include_in_schema=False):
            return None

    sys.modules["prometheus_fastapi_instrumentator"] = types.SimpleNamespace(
        Instrumentator=_StubInstrumentator
    )

if "prometheus_client" not in sys.modules:
    class _StubHistogram:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def observe(self, value):
            return None

    sys.modules["prometheus_client"] = types.SimpleNamespace(Histogram=_StubHistogram)

from main import app

sys.path.append(str(Path(__file__).parent.parent))

# ------------------ cliente ------------------
@pytest.fixture
def client():
    return TestClient(app)

# ------------------ env común ------------------
@pytest.fixture(autouse=True)
def patch_env(monkeypatch):
    monkeypatch.setenv("ACCESS_TOKEN_SECRET_KEY", "test-secret-key-12345")
    monkeypatch.setenv("ALGORITHM", "HS256")
    monkeypatch.setenv("AUTH_AUDIENCE", "anb-api")
    monkeypatch.setenv("AUTH_ISSUER", "anb-auth")

# ------------------ parchea decode del middleware ------------------
@pytest.fixture(autouse=True)
def bypass_jwt_verify(monkeypatch):
    """
    Evita 401 del middleware en pruebas: si hay Bearer token,
    devolvemos claims sin validar firma/audience/issuer.
    Los tests que NECESITAN error ya hacen su propio patch.
    """
    def _fake_decode(token, key, algorithms=None, audience=None, issuer=None, options=None):
        # jose permite leer claims sin verificar:
        return jwt.get_unverified_claims(token)
    monkeypatch.setattr("app.core.auth_middleware.jwt.decode", _fake_decode)

# ------------------ FIXTURE make_token ------------------
@pytest.fixture
def make_token():
    secret = os.getenv("ACCESS_TOKEN_SECRET_KEY", "test-secret-key-12345")
    alg = os.getenv("ALGORITHM", "HS256")
    aud = os.getenv("AUTH_AUDIENCE", "anb-api")
    iss = os.getenv("AUTH_ISSUER", "anb-auth")

    def _emit(user_id="test-user-1", ttl_seconds=3600):
        now = int(time.time())
        payload = {
            "sub": user_id,
            "aud": aud,
            "iss": iss,
            "iat": now,
            "exp": now + ttl_seconds,
        }
        return jwt.encode(payload, secret, algorithm=alg)
    return _emit

# ------------------ inyecta request.state.user una sola vez ------------------
if not getattr(app.state, "_user_injected_mw", False):
    @app.middleware("http")
    async def _inject_user(request, call_next):
        if not getattr(request.state, "user", None):
            request.state.user = {
                "user_id": "test-user-1",
                "first_name": "Test",
                "last_name": "User",
                "city": "Bogotá",
            }
        return await call_next(request)
    app.state._user_injected_mw = True
