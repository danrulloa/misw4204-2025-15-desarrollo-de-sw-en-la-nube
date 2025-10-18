"""
Configuración de fixtures para pytest
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

# Constantes para tests
TEST_USER_EMAIL = "pedro@test.com"
TEST_USER_PASSWORD = "SecurePass123"


@pytest.fixture
def mock_db_session():
    """
    Fixture que proporciona un mock de AsyncSession para tests
    """
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def valid_user_signup_data():
    """
    Fixture con datos válidos para registro de usuario
    """
    return {
        "first_name": "Pedro",
        "last_name": "Gomez",
        "email": TEST_USER_EMAIL,
        "password1": TEST_USER_PASSWORD,
        "password2": TEST_USER_PASSWORD,
        "city": "Bogotá",
        "country": "Colombia"
    }


@pytest.fixture
def valid_user_login_data():
    """
    Fixture con datos válidos para login
    """
    return {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }


@pytest.fixture
def mock_user():
    """
    Fixture que proporciona un mock de User para tests
    """
    user = MagicMock()
    user.id = 1
    user.email = TEST_USER_EMAIL
    user.first_name = "Pedro"
    user.last_name = "Gomez"
    user.city = "Bogotá"
    user.country = "Colombia"
    user.tenant_id = 0
    user.hashed_password = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWPnoMnmS9C"  # Hash de "SecurePass123"
    user.groups = []
    return user


@pytest.fixture
def mock_session_token():
    """
    Fixture que proporciona un mock de Session para tests
    """
    session = MagicMock()
    session.id = 1
    session.user_id = 1
    session.session_token = "mock_access_token"
    session.refresh_token = "mock_refresh_token"
    session.session_expires_at = datetime.now(timezone.utc)
    session.refresh_expires_at = datetime.now(timezone.utc)
    return session
