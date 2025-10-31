
from app.services.storage.base import StoragePort
from app.services.storage.local import LocalStorageAdapter
from app.services.storage.s3 import S3StorageAdapter
from app.config import settings

def get_storage() -> StoragePort:
    if settings.STORAGE_BACKEND == "s3":
        return S3StorageAdapter(
            bucket=settings.S3_BUCKET,
            prefix=settings.S3_PREFIX,
            region=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            force_path_style=settings.S3_FORCE_PATH_STYLE,
            verify_ssl=settings.S3_VERIFY_SSL,
        )
    return LocalStorageAdapter()
