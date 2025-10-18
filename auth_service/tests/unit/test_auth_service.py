"""
Tests para AuthService
"""

import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.authentication.auth_service import AuthService
from jose import jwt
import os


class TestAuthServicePasswordMethods:
    """Tests para métodos de contraseñas"""

    def test_verify_password_correct(self):
        """Test verificar contraseña correcta"""
        plain_password = "SecurePass123"
        hashed_password = AuthService.get_password_hash(plain_password)

        assert AuthService.verify_password(plain_password, hashed_password) is True

    def test_verify_password_incorrect(self):
        """Test verificar contraseña incorrecta"""
        plain_password = "SecurePass123"
        wrong_password = "WrongPass456"
        hashed_password = AuthService.get_password_hash(plain_password)

        assert AuthService.verify_password(wrong_password, hashed_password) is False

    def test_get_password_hash_generates_valid_hash(self):
        """Test que get_password_hash genera un hash válido"""
        password = "SecurePass123"
        hashed = AuthService.get_password_hash(password)

        assert hashed is not None
        assert hashed != password  # El hash no debe ser igual a la contraseña
        assert hashed.startswith("$2b$")  # bcrypt hash prefix


class TestAuthServiceTokenMethods:
    """Tests para métodos de tokens"""

    def test_create_access_token_without_expires_delta(self, mock_user):
        """Test crear access token sin expires_delta"""
        data = {
            "sub": mock_user.email,
            "user_id": mock_user.id
        }

        token, expiration = AuthService.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert expiration is not None

        # Decodificar y verificar contenido
        decoded = jwt.decode(
            token,
            os.environ["ACCESS_TOKEN_SECRET_KEY"],
            algorithms=[os.environ["ALGORITHM"]]
        )
        assert decoded["sub"] == mock_user.email
        assert decoded["user_id"] == mock_user.id
        assert decoded["token_type"] == "access"

    def test_create_access_token_with_expires_delta(self, mock_user):
        """Test crear access token con expires_delta"""
        data = {
            "sub": mock_user.email,
            "user_id": mock_user.id
        }
        expires_delta = timedelta(minutes=30)

        token, expiration = AuthService.create_access_token(data, expires_delta)

        assert token is not None
        assert isinstance(token, str)

        decoded = jwt.decode(
            token,
            os.environ["ACCESS_TOKEN_SECRET_KEY"],
            algorithms=[os.environ["ALGORITHM"]]
        )
        assert decoded["token_type"] == "access"

    def test_create_refresh_token_without_expires_delta(self, mock_user):
        """Test crear refresh token sin expires_delta"""
        data = {
            "sub": mock_user.email,
            "user_id": mock_user.id
        }

        token, expiration = AuthService.create_refresh_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert expiration is not None

        # Decodificar y verificar contenido
        decoded = jwt.decode(
            token,
            os.environ["REFRESH_TOKEN_SECRET_KEY"],
            algorithms=[os.environ["ALGORITHM"]]
        )
        assert decoded["sub"] == mock_user.email
        assert decoded["user_id"] == mock_user.id
        assert decoded["token_type"] == "refresh"

    def test_create_refresh_token_with_expires_delta(self, mock_user):
        """Test crear refresh token con expires_delta"""
        data = {
            "sub": mock_user.email,
            "user_id": mock_user.id
        }
        expires_delta = timedelta(days=7)

        token, expiration = AuthService.create_refresh_token(data, expires_delta)

        assert token is not None
        assert isinstance(token, str)

        decoded = jwt.decode(
            token,
            os.environ["REFRESH_TOKEN_SECRET_KEY"],
            algorithms=[os.environ["ALGORITHM"]]
        )
        assert decoded["token_type"] == "refresh"


class TestAuthServiceUserMethods:
    """Tests para métodos de usuario"""

    @pytest.mark.asyncio
    async def test_get_user_found(self, mock_db_session, mock_user):
        """Test obtener usuario existente"""
        # Mock del resultado de la query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db_session.execute.return_value = mock_result

        user = await AuthService.get_user(mock_user.email, mock_db_session)

        assert user is not None
        assert user.email == mock_user.email
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_db_session):
        """Test obtener usuario no existente"""
        # Mock del resultado de la query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        user = await AuthService.get_user("nonexistent@test.com", mock_db_session)

        assert user is None
        assert mock_db_session.execute.called

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mock_db_session, mock_user):
        """Test autenticar usuario con credenciales correctas"""
        # Mock get_user
        with patch.object(AuthService, 'get_user', return_value=mock_user):
            # Mock verify_password
            with patch.object(AuthService, 'verify_password', return_value=True):
                user = await AuthService.authenticate_user(
                    mock_user.email,
                    "SecurePass123",
                    mock_db_session
                )

                assert user is not None
                assert user.email == mock_user.email

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, mock_db_session, mock_user):
        """Test autenticar usuario con contraseña incorrecta"""
        # Mock get_user
        with patch.object(AuthService, 'get_user', return_value=mock_user):
            # Mock verify_password
            with patch.object(AuthService, 'verify_password', return_value=False):
                user = await AuthService.authenticate_user(
                    mock_user.email,
                    "WrongPassword",
                    mock_db_session
                )

                assert user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_exists(self, mock_db_session):
        """Test autenticar usuario que no existe"""
        # Mock get_user retornando None
        with patch.object(AuthService, 'get_user', return_value=None):
            user = await AuthService.authenticate_user(
                "nonexistent@test.com",
                "AnyPassword",
                mock_db_session
            )

            assert user is None


class TestAuthServiceSessionMethods:
    """Tests para métodos de sesiones"""

    @pytest.mark.asyncio
    async def test_create_session(self, mock_db_session):
        """Test crear sesión con tokens"""
        from datetime import datetime, timezone, timedelta

        user_id = 1
        access_token = "mock_access_token"
        refresh_token = "mock_refresh_token"
        access_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        refresh_expires = datetime.now(timezone.utc) + timedelta(days=7)

        # Mock flush y commit
        mock_db_session.flush = AsyncMock()
        mock_db_session.commit = AsyncMock()

        await AuthService.create_session(
            db=mock_db_session,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires,
            refresh_expires_at=refresh_expires
        )

        # Verificar que se llamó add dos veces (Session y RefreshToken)
        assert mock_db_session.add.call_count == 2
        assert mock_db_session.flush.called
        assert mock_db_session.commit.called
