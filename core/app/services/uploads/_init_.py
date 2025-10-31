from app.services.uploads.base import UploadServicePort
from app.services.uploads.local import LocalUploadService


def get_upload_service() -> UploadServicePort:
    # Por ahora solo un backend local. En el futuro se puede
    # parametrizar por settings (p. ej., S3, etc.).
    # if settings.UPLOADS_BACKEND == "s3":
    #     return S3UploadService(...)
    return LocalUploadService()
