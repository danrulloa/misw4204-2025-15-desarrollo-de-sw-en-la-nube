"""
Módulo de schemas Pydantic
Define modelos de request y response para la API.
"""

from app.schemas.auth import (
    UserSignupRequest,
    UserLoginRequest,
    TokenResponse,
    UserSignupResponse
)
from app.schemas.video import (
    VideoStatus,
    VideoUploadResponse,
    VideoResponse,
    VideoListItemResponse,
    VideoDeleteResponse
)
from app.schemas.vote import (
    VoteResponse,
    PublicVideoResponse,
    RankingItemResponse,
    RankingResponse
)
from app.schemas.common import (
    ErrorResponse,
    ValidationErrorResponse,
    MessageResponse
)

__all__ = [
    # Auth schemas
    "UserSignupRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserSignupResponse",
    # Video schemas
    "VideoStatus",
    "VideoUploadResponse",
    "VideoResponse",
    "VideoListItemResponse",
    "VideoDeleteResponse",
    # Vote schemas
    "VoteResponse",
    "PublicVideoResponse",
    "RankingItemResponse",
    "RankingResponse",
    # Common schemas
    "ErrorResponse",
    "ValidationErrorResponse",
    "MessageResponse",
]
