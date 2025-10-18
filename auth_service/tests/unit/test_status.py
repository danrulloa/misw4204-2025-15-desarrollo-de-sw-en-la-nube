"""
Tests adicionales para componentes del sistema
"""

from app.db.models.user import User
from app.db.models.session import Session
from app.db.models.refreshToken import RefreshToken


class TestModels:
    """Tests básicos de modelos"""

    def test_user_model_instantiation(self):
        """Test que el modelo User puede instanciarse"""
        user = User(
            email="test@example.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="User"
        )
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"

    def test_session_model_instantiation(self):
        """Test que el modelo Session puede instanciarse"""
        session = Session(
            user_id=1,
            session_token="token",
            refresh_token="refresh"
        )
        assert session.user_id == 1
        assert session.session_token == "token"
        assert session.refresh_token == "refresh"

    def test_refresh_token_model_instantiation(self):
        """Test que el modelo RefreshToken puede instanciarse"""
        refresh = RefreshToken(
            session_id=1,
            token="refresh_token_value"
        )
        assert refresh.session_id == 1
        assert refresh.token == "refresh_token_value"
