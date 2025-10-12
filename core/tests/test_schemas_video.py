"""
Tests para schemas de videos
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.schemas.video import (
    VideoStatus,
    VideoUploadResponse,
    VideoResponse,
    VideoListItemResponse,
    VideoDeleteResponse
)


class TestVideoStatus:
    """Tests para el enum VideoStatus"""
    
    def test_valid_statuses(self):
        """Test con estados válidos"""
        assert VideoStatus.UPLOADED == "uploaded"
        assert VideoStatus.PROCESSING == "processing"
        assert VideoStatus.PROCESSED == "processed"
        assert VideoStatus.FAILED == "failed"
    
    def test_status_values(self):
        """Test que los valores son strings"""
        for status in VideoStatus:
            assert isinstance(status.value, str)


class TestVideoUploadResponse:
    """Tests para el schema de respuesta de upload"""
    
    def test_valid_upload_response(self):
        """Test con respuesta válida"""
        response = VideoUploadResponse(
            message="Video subido correctamente",
            video_id="abc123",
            task_id="task456"
        )
        assert response.message == "Video subido correctamente"
        assert response.video_id == "abc123"
        assert response.task_id == "task456"
    
    def test_missing_required_fields(self):
        """Test con campos requeridos faltantes"""
        with pytest.raises(ValidationError):
            VideoUploadResponse(message="Test")


class TestVideoResponse:
    """Tests para el schema de respuesta de video"""
    
    def test_valid_video_response(self):
        """Test con video válido"""
        now = datetime.utcnow()
        video = VideoResponse(
            video_id="abc123",
            title="Mi mejor tiro",
            status=VideoStatus.PROCESSED,
            uploaded_at=now,
            processed_at=now,
            original_url="http://example.com/original.mp4",
            processed_url="http://example.com/processed.mp4",
            votes=10
        )
        assert video.video_id == "abc123"
        assert video.title == "Mi mejor tiro"
        assert video.status == VideoStatus.PROCESSED
        assert video.votes == 10
    
    def test_optional_fields_none(self):
        """Test con campos opcionales en None"""
        now = datetime.utcnow()
        video = VideoResponse(
            video_id="abc123",
            title="Test",
            status=VideoStatus.UPLOADED,
            uploaded_at=now
        )
        assert video.processed_at is None
        assert video.original_url is None
        assert video.processed_url is None
        assert video.votes == 0
    
    def test_invalid_status(self):
        """Test con estado inválido"""
        now = datetime.utcnow()
        with pytest.raises(ValidationError):
            VideoResponse(
                video_id="abc123",
                title="Test",
                status="invalid_status",
                uploaded_at=now
            )


class TestVideoListItemResponse:
    """Tests para el schema de item de lista"""
    
    def test_valid_list_item(self):
        """Test con item válido"""
        now = datetime.utcnow()
        item = VideoListItemResponse(
            video_id="123",
            title="Test Video",
            status=VideoStatus.PROCESSED,
            uploaded_at=now,
            processed_at=now,
            processed_url="http://example.com/video.mp4"
        )
        assert item.video_id == "123"
        assert item.title == "Test Video"


class TestVideoDeleteResponse:
    """Tests para el schema de respuesta de eliminación"""
    
    def test_valid_delete_response(self):
        """Test con respuesta válida"""
        response = VideoDeleteResponse(
            message="Video eliminado exitosamente",
            video_id="abc123"
        )
        assert response.message == "Video eliminado exitosamente"
        assert response.video_id == "abc123"
