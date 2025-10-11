"""
Tests para schemas de autenticación
"""

import pytest
from pydantic import ValidationError
from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserSignupResponse
)


class TestUserSignupRequest:
    """Tests para el schema de registro de usuario"""
    
    def test_valid_signup_data(self, valid_user_signup_data):
        """Test con datos válidos"""
        user = UserSignupRequest(**valid_user_signup_data)
        assert user.first_name == "Pedro"
        assert user.last_name == "Gomez"
        assert user.email == "a@b.com"
        assert user.city == "Bogotá"
        assert user.country == "Colombia"
    
    def test_email_lowercase_conversion(self):
        """Test que el email se convierte a minúsculas"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "JOHN.DOE@EXAMPLE.COM",
            "password1": "SecurePass123",
            "password2": "SecurePass123",
            "city": "Bogotá",
            "country": "Colombia"
        }
        user = UserSignupRequest(**data)
        assert user.email == "john.doe@example.com"
    
    def test_invalid_email_format(self, valid_user_signup_data):
        """Test con email inválido"""
        valid_user_signup_data["email"] = "invalid-email"
        with pytest.raises(ValidationError) as exc_info:
            UserSignupRequest(**valid_user_signup_data)
        assert "email" in str(exc_info.value)
    
    def test_missing_required_fields(self):
        """Test con campos requeridos faltantes"""
        with pytest.raises(ValidationError) as exc_info:
            UserSignupRequest(first_name="John")
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_password_too_short(self, valid_user_signup_data):
        """Test con contraseña muy corta"""
        valid_user_signup_data["password1"] = "short"
        valid_user_signup_data["password2"] = "short"
        with pytest.raises(ValidationError) as exc_info:
            UserSignupRequest(**valid_user_signup_data)
        assert "password1" in str(exc_info.value)
    
    def test_empty_string_fields(self, valid_user_signup_data):
        """Test con campos vacíos"""
        valid_user_signup_data["first_name"] = ""
        with pytest.raises(ValidationError):
            UserSignupRequest(**valid_user_signup_data)


class TestUserLoginRequest:
    """Tests para el schema de login"""
    
    def test_valid_login_data(self, valid_user_login_data):
        """Test con datos válidos"""
        login = UserLoginRequest(**valid_user_login_data)
        assert login.email == "a@b.com"
        assert login.password == "123Qwweasd"
    
    def test_email_lowercase_conversion(self):
        """Test que el email se convierte a minúsculas"""
        data = {
            "email": "JOHN.DOE@EXAMPLE.COM",
            "password": "SecurePass123"
        }
        login = UserLoginRequest(**data)
        assert login.email == "john.doe@example.com"
    
    def test_invalid_email(self):
        """Test con email inválido"""
        with pytest.raises(ValidationError):
            UserLoginRequest(email="invalid", password="pass")


class TestTokenResponse:
    """Tests para el schema de respuesta de token"""
    
    def test_valid_token_response(self):
        """Test con token válido"""
        token = TokenResponse(access_token="eyJ0eXAiOiJKV1QiLCJhbGci...")
        assert token.access_token == "eyJ0eXAiOiJKV1QiLCJhbGci..."
        assert token.token_type == "Bearer"
        assert token.expires_in == 3600
    
    def test_custom_expiration(self):
        """Test con tiempo de expiración personalizado"""
        token = TokenResponse(
            access_token="token123",
            expires_in=7200
        )
        assert token.expires_in == 7200


class TestUserSignupResponse:
    """Tests para el schema de respuesta de registro"""
    
    def test_valid_signup_response(self):
        """Test con respuesta válida"""
        response = UserSignupResponse(
            message="Usuario creado exitosamente",
            user_id=1,
            email="john@example.com"
        )
        assert response.message == "Usuario creado exitosamente"
        assert response.user_id == 1
        assert response.email == "john@example.com"
