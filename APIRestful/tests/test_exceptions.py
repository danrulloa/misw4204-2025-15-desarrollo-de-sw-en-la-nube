"""
Tests para excepciones personalizadas
"""

import pytest
from app.exceptions import (
    APIException,
    UnauthorizedError,
    InvalidCredentialsError,
    TokenExpiredError,
    ForbiddenError,
    NotFoundError,
    VideoNotFoundError,
    UserNotFoundError,
    BadRequestError,
    ValidationError,
    DuplicateEmailError,
    PasswordMismatchError,
    InvalidFileTypeError,
    FileSizeExceededError,
    VideoDurationError,
    ConflictError,
    AlreadyVotedError,
    VideoNotProcessedError,
    CannotDeleteVideoError,
    InternalServerError,
    StorageError,
    ProcessingError,
)


class TestAPIException:
    """Tests para la excepción base"""
    
    def test_api_exception_creation(self):
        """Test creación de excepción base"""
        exc = APIException("Test error", status_code=400, error_code="TEST_ERROR")
        assert exc.message == "Test error"
        assert exc.status_code == 400
        assert exc.error_code == "TEST_ERROR"
    
    def test_api_exception_default_status(self):
        """Test status code por defecto"""
        exc = APIException("Test")
        assert exc.status_code == 500


class TestAuthExceptions:
    """Tests para excepciones de autenticación"""
    
    def test_unauthorized_error(self):
        """Test UnauthorizedError"""
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"
        assert "autorizado" in exc.message.lower()
    
    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError"""
        exc = InvalidCredentialsError()
        assert exc.status_code == 401
        assert exc.error_code == "INVALID_CREDENTIALS"
    
    def test_token_expired_error(self):
        """Test TokenExpiredError"""
        exc = TokenExpiredError()
        assert exc.status_code == 401
        assert exc.error_code == "TOKEN_EXPIRED"


class TestAuthorizationExceptions:
    """Tests para excepciones de autorización"""
    
    def test_forbidden_error(self):
        """Test ForbiddenError"""
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"


class TestNotFoundExceptions:
    """Tests para excepciones de recursos no encontrados"""
    
    def test_not_found_error(self):
        """Test NotFoundError"""
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
    
    def test_video_not_found_error(self):
        """Test VideoNotFoundError"""
        exc = VideoNotFoundError("abc123")
        assert exc.status_code == 404
        assert exc.error_code == "VIDEO_NOT_FOUND"
        assert "abc123" in exc.message
    
    def test_user_not_found_error_with_email(self):
        """Test UserNotFoundError con email"""
        exc = UserNotFoundError(email="test@example.com")
        assert exc.status_code == 404
        assert "test@example.com" in exc.message
    
    def test_user_not_found_error_with_id(self):
        """Test UserNotFoundError con ID"""
        exc = UserNotFoundError(user_id="123")
        assert "123" in exc.message


class TestBadRequestExceptions:
    """Tests para excepciones de solicitud incorrecta"""
    
    def test_bad_request_error(self):
        """Test BadRequestError"""
        exc = BadRequestError()
        assert exc.status_code == 400
        assert exc.error_code == "BAD_REQUEST"
    
    def test_validation_error(self):
        """Test ValidationError"""
        exc = ValidationError("Campo inválido", field="email")
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.field == "email"
    
    def test_duplicate_email_error(self):
        """Test DuplicateEmailError"""
        exc = DuplicateEmailError("test@example.com")
        assert exc.status_code == 400
        assert exc.error_code == "DUPLICATE_EMAIL"
        assert "test@example.com" in exc.message
    
    def test_password_mismatch_error(self):
        """Test PasswordMismatchError"""
        exc = PasswordMismatchError()
        assert exc.status_code == 400
        assert exc.error_code == "PASSWORD_MISMATCH"
    
    def test_invalid_file_type_error(self):
        """Test InvalidFileTypeError"""
        exc = InvalidFileTypeError(["mp4", "avi"])
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_FILE_TYPE"
        assert "mp4" in exc.message
        assert "avi" in exc.message
    
    def test_file_size_exceeded_error(self):
        """Test FileSizeExceededError"""
        exc = FileSizeExceededError(100)
        assert exc.status_code == 400
        assert exc.error_code == "FILE_SIZE_EXCEEDED"
        assert "100" in exc.message
    
    def test_video_duration_error(self):
        """Test VideoDurationError"""
        exc = VideoDurationError(20, 60)
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_VIDEO_DURATION"
        assert "20" in exc.message
        assert "60" in exc.message


class TestConflictExceptions:
    """Tests para excepciones de conflicto"""
    
    def test_conflict_error(self):
        """Test ConflictError"""
        exc = ConflictError()
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"
    
    def test_already_voted_error(self):
        """Test AlreadyVotedError"""
        exc = AlreadyVotedError()
        assert exc.status_code == 409
        assert exc.error_code == "ALREADY_VOTED"
    
    def test_video_not_processed_error(self):
        """Test VideoNotProcessedError"""
        exc = VideoNotProcessedError()
        assert exc.status_code == 409
        assert exc.error_code == "VIDEO_NOT_PROCESSED"
    
    def test_cannot_delete_video_error(self):
        """Test CannotDeleteVideoError"""
        exc = CannotDeleteVideoError("Video en votación")
        assert exc.status_code == 409
        assert exc.error_code == "CANNOT_DELETE_VIDEO"
        assert "Video en votación" in exc.message


class TestServerExceptions:
    """Tests para excepciones de servidor"""
    
    def test_internal_server_error(self):
        """Test InternalServerError"""
        exc = InternalServerError()
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_SERVER_ERROR"
    
    def test_storage_error(self):
        """Test StorageError"""
        exc = StorageError()
        assert exc.status_code == 500
        assert exc.error_code == "STORAGE_ERROR"
    
    def test_processing_error(self):
        """Test ProcessingError"""
        exc = ProcessingError()
        assert exc.status_code == 500
        assert exc.error_code == "PROCESSING_ERROR"
