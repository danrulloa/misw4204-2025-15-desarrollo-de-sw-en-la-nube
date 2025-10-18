"""
Tests para schemas de usuario
"""

import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate, UserBasic


class TestUserCreate:
    """Tests para el schema UserCreate"""

    def test_valid_user_creation(self, valid_user_signup_data):
        """Test con datos válidos de usuario"""
        user = UserCreate(**valid_user_signup_data)
        assert user.first_name == "Pedro"
        assert user.last_name == "Gomez"
        assert user.email == "pedro@test.com"
        assert user.password1 == "SecurePass123"
        assert user.password2 == "SecurePass123"
        assert user.city == "Bogotá"
        assert user.country == "Colombia"

    def test_passwords_do_not_match(self):
        """Test cuando las contraseñas no coinciden"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="Pedro",
                last_name="Gomez",
                email="pedro@test.com",
                password1="SecurePass123",
                password2="DifferentPass456",
                city="Bogotá"
            )
        assert "Las contraseñas no coinciden" in str(exc_info.value)

    def test_password_too_short(self):
        """Test cuando la contraseña es menor a 8 caracteres"""
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(
                first_name="Pedro",
                last_name="Gomez",
                email="pedro@test.com",
                password1="Short1",
                password2="Short1",
                city="Bogotá"
            )
        assert "debe tener al menos 8 caracteres" in str(exc_info.value)

    def test_invalid_email(self):
        """Test con email inválido"""
        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Pedro",
                last_name="Gomez",
                email="not-an-email",
                password1="SecurePass123",
                password2="SecurePass123"
            )

    def test_missing_required_fields(self):
        """Test con campos requeridos faltantes"""
        with pytest.raises(ValidationError):
            UserCreate(
                first_name="Pedro"
                # Faltan campos requeridos
            )

    def test_optional_fields_can_be_none(self):
        """Test que los campos opcionales pueden ser None"""
        user = UserCreate(
            first_name="Pedro",
            last_name="Gomez",
            email="pedro@test.com",
            password1="SecurePass123",
            password2="SecurePass123",
            city=None,
            country=None
        )
        assert user.city is None
        assert user.country is None


class TestUserBasic:
    """Tests para el schema UserBasic"""

    def test_valid_user_basic(self):
        """Test con datos válidos"""
        user = UserBasic(
            id=1,
            username="pedro"
        )
        assert user.id == 1
        assert user.username == "pedro"

    def test_missing_required_fields_user_basic(self):
        """Test con campos requeridos faltantes"""
        with pytest.raises(ValidationError):
            UserBasic(id=1)  # Falta username
