
from app.services.storage.base import StoragePort
from app.services.storage.local import LocalStorageAdapter
from app.config import settings

def get_storage() -> StoragePort:
    if settings.STORAGE_BACKEND == "local":
        return LocalStorageAdapter()
    # futuro:
    # if settings.STORAGE_BACKEND == "s3":
    #     return S3StorageAdapter(...)
    return LocalStorageAdapter()