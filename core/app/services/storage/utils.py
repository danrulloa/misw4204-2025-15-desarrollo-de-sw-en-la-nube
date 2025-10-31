from pathlib import Path as PathLib
from app.config import settings


def abs_storage_path(rel_path: str) -> PathLib:
    """Convierte rutas relativas persistidas a rutas absolutas del contenedor.

    - '/uploads/...'   -> settings.UPLOAD_DIR
    - '/processed/...' -> settings.PROCESSED_DIR
    - otro             -> se resuelve bajo UPLOAD_DIR
    """
    if not rel_path:
        return PathLib("/non/existent")
    if rel_path.startswith("/uploads"):
        return PathLib(rel_path.replace("/uploads", settings.UPLOAD_DIR, 1))
    if rel_path.startswith("/processed"):
        return PathLib(rel_path.replace("/processed", settings.PROCESSED_DIR, 1))
    return PathLib(settings.UPLOAD_DIR.rstrip("/")) / rel_path.lstrip("/")

