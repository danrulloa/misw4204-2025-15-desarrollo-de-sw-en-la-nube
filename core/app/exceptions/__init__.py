"""
Módulo de excepciones personalizadas
Excepciones específicas de la aplicación
"""

from app.exceptions.custom_exceptions import (
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

from app.exceptions.handlers import (
    api_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)

__all__ = [
    # Base
    "APIException",
    # Auth (401)
    "UnauthorizedError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    # Authorization (403)
    "ForbiddenError",
    # Not Found (404)
    "NotFoundError",
    "VideoNotFoundError",
    "UserNotFoundError",
    # Bad Request (400)
    "BadRequestError",
    "ValidationError",
    "DuplicateEmailError",
    "PasswordMismatchError",
    "InvalidFileTypeError",
    "FileSizeExceededError",
    "VideoDurationError",
    # Conflict (409)
    "ConflictError",
    "AlreadyVotedError",
    "VideoNotProcessedError",
    "CannotDeleteVideoError",
    # Server Error (500)
    "InternalServerError",
    "StorageError",
    "ProcessingError",
    # Handlers
    "api_exception_handler",
    "validation_exception_handler",
    "general_exception_handler",
]
