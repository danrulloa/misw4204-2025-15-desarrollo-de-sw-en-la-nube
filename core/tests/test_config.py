"""
Tests para configuración de la aplicación
"""

import pytest
from app.config import Settings


class TestSettings:
    """Tests para la configuración"""
    
    def test_default_settings(self):
        """Test configuración por defecto"""
        settings = Settings()
        assert settings.APP_NAME == "ANB Rising Stars API"
        assert settings.API_VERSION == "v1"
        assert settings.MAX_UPLOAD_SIZE_MB == 100
        assert settings.MIN_VIDEO_DURATION_SECONDS == 20
        assert settings.MAX_VIDEO_DURATION_SECONDS == 60
    
    def test_allowed_video_formats(self):
        """Test formatos de video permitidos"""
        settings = Settings()
        assert "mp4" in settings.ALLOWED_VIDEO_FORMATS
        assert "avi" in settings.ALLOWED_VIDEO_FORMATS
        assert "mov" in settings.ALLOWED_VIDEO_FORMATS
    
    def test_storage_paths(self):
        """Test rutas de almacenamiento"""
        settings = Settings()
        assert settings.UPLOAD_DIR == "/app/storage/uploads"
        assert settings.PROCESSED_DIR == "/app/storage/processed"
