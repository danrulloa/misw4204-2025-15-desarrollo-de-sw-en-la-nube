"""
Tests para UserService
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from app.services.authentication.user_service import UserService
from app.schemas.user import UserCreate
from app.db.models.user import User


class TestUserServiceCreateUser:
    """Tests para el método create_user"""

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_db_session, valid_user_signup_data):
        """Test crear usuario exitosamente"""
        # Mock: email no existe
        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = None

        # Mock: grupo default existe
        mock_group = MagicMock()
        mock_group.name = "user"
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = mock_group

        # Configurar execute para retornar diferentes resultados
        mock_db_session.execute.side_effect = [mock_check_result, mock_group_result]

        # Mock del hash de contraseña - path correcto desde donde se importa
        with patch('app.services.authentication.auth_service.AuthService.get_password_hash',
                   return_value="hashed_password"):

            user_data = UserCreate(**valid_user_signup_data)
            new_user = await UserService.create_user(user_data, mock_db_session)

            # Verificaciones
            assert mock_db_session.add.called
            assert mock_db_session.commit.called
            assert mock_db_session.refresh.called

    @pytest.mark.asyncio
    async def test_create_user_email_already_exists(self, mock_db_session, valid_user_signup_data):
        """Test crear usuario con email que ya existe"""
        # Mock: email ya existe
        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = 1  # ID del usuario existente
        mock_db_session.execute.return_value = mock_check_result

        user_data = UserCreate(**valid_user_signup_data)

        with pytest.raises(HTTPException) as exc_info:
            await UserService.create_user(user_data, mock_db_session)

        assert exc_info.value.status_code == 400
        assert "ya está registrado" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_create_user_without_default_group(self, mock_db_session, valid_user_signup_data):
        """Test crear usuario cuando no existe grupo por defecto"""
        # Mock: email no existe
        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = None

        # Mock: grupo default NO existe
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_check_result, mock_group_result]

        # Mock del hash de contraseña - path correcto
        with patch('app.services.authentication.auth_service.AuthService.get_password_hash',
                   return_value="hashed_password"):

            user_data = UserCreate(**valid_user_signup_data)
            new_user = await UserService.create_user(user_data, mock_db_session)

            # Debe crear el usuario sin grupo
            assert mock_db_session.add.called
            assert mock_db_session.commit.called

    @pytest.mark.asyncio
    async def test_create_user_integrity_error(self, mock_db_session, valid_user_signup_data):
        """Test crear usuario con IntegrityError"""
        # Mock: email no existe en la verificación inicial
        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = None

        # Mock: grupo default existe
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = MagicMock()

        mock_db_session.execute.side_effect = [mock_check_result, mock_group_result]

        # Mock: IntegrityError en commit
        mock_orig = MagicMock()
        mock_orig.__str__ = MagicMock(return_value="duplicate key value violates unique constraint email")
        mock_db_session.commit.side_effect = IntegrityError(
            "statement", "params", mock_orig
        )

        # Mock del hash de contraseña - path correcto
        with patch('app.services.authentication.auth_service.AuthService.get_password_hash',
                   return_value="hashed_password"):

            user_data = UserCreate(**valid_user_signup_data)

            with pytest.raises(HTTPException) as exc_info:
                await UserService.create_user(user_data, mock_db_session)

            assert exc_info.value.status_code == 400
            assert "ya está registrado" in exc_info.value.detail or "error de base de datos" in exc_info.value.detail
            assert mock_db_session.rollback.called

    @pytest.mark.asyncio
    async def test_create_user_uses_password1_field(self, mock_db_session):
        """Test que create_user usa password1 del UserCreate"""
        # Mock: email no existe
        mock_check_result = MagicMock()
        mock_check_result.scalar_one_or_none.return_value = None

        # Mock: grupo default no existe (para simplificar)
        mock_group_result = MagicMock()
        mock_group_result.scalar_one_or_none.return_value = None

        mock_db_session.execute.side_effect = [mock_check_result, mock_group_result]

        test_password = "TestPassword123"

        # Mock del hash de contraseña y capturar el argumento - path correcto
        with patch('app.services.authentication.auth_service.AuthService.get_password_hash',
                   return_value="hashed_test") as mock_hash:

            user_data = UserCreate(
                first_name="Test",
                last_name="User",
                email="test@example.com",
                password1=test_password,
                password2=test_password
            )

            await UserService.create_user(user_data, mock_db_session)

            # Verificar que get_password_hash fue llamado con password1
            mock_hash.assert_called_once_with(test_password)
