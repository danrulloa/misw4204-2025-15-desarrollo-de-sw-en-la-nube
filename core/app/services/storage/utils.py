"""
Utilities para resolver rutas de almacenamiento (local y S3).
"""

from pathlib import Path as PathLib
from urllib.parse import urlparse

from app.config import settings

# Prefijos web usados en la aplicación — usar constantes evita duplicación y errores de mantenimiento
UPLOAD_WEB_PREFIX = "/uploads"
PROCESSED_WEB_PREFIX = "/processed"


def abs_storage_path(rel_path: str) -> PathLib:
    """Convierte rutas relativas persistidas a rutas absolutas del contenedor.

    - '/uploads/...'   -> settings.UPLOAD_DIR
    - '/processed/...' -> settings.PROCESSED_DIR
    - otro             -> se resuelve bajo UPLOAD_DIR
    """
    if not rel_path:
        return PathLib("/non/existent")

    rel = rel_path.strip()

    if rel.startswith(UPLOAD_WEB_PREFIX):
        # remover prefijo web y unir con la carpeta real
        rel_part = rel.removeprefix(UPLOAD_WEB_PREFIX).lstrip("/")
        return PathLib(settings.UPLOAD_DIR.rstrip("/")) / rel_part if rel_part else PathLib(settings.UPLOAD_DIR)

    if rel.startswith(PROCESSED_WEB_PREFIX):
        rel_part = rel.removeprefix(PROCESSED_WEB_PREFIX).lstrip("/")
        return PathLib(settings.PROCESSED_DIR.rstrip("/")) / rel_part if rel_part else PathLib(settings.PROCESSED_DIR)

    return PathLib(settings.UPLOAD_DIR.rstrip("/")) / rel.lstrip("/")


def _normalize_local_web_path(path: str) -> str | None:
    """Normaliza rutas locales a la convención web (UPLOAD_WEB_PREFIX, PROCESSED_WEB_PREFIX).

    - convierte separadores Windows a '/'
    - reemplaza raíces locales (settings) por el prefijo web correspondiente
    - si la ruta ya usa el prefijo web, la devuelve tal cual
    - en cualquier otro caso devuelve una ruta con prefijo '/'
    """
    if not path:
        return None

    path = path.replace("\\", "/")

    if path.startswith(UPLOAD_WEB_PREFIX) or path.startswith(PROCESSED_WEB_PREFIX):
        return path

    uploads_root = (settings.UPLOAD_DIR or "").rstrip("/")
    processed_root = (settings.PROCESSED_DIR or "").rstrip("/")

    if uploads_root and path.startswith(uploads_root):
        rel = path[len(uploads_root) :].lstrip("/")
        return f"{UPLOAD_WEB_PREFIX}/{rel}" if rel else UPLOAD_WEB_PREFIX

    if processed_root and path.startswith(processed_root):
        rel = path[len(processed_root) :].lstrip("/")
        return f"{PROCESSED_WEB_PREFIX}/{rel}" if rel else PROCESSED_WEB_PREFIX

    return f"/{path.lstrip('/')}"


def _parse_s3_path(path: str) -> tuple[str, str]:
    """Devuelve (bucket, key) a partir de s3://bucket/key."""
    remainder = path.removeprefix("s3://")
    parts = remainder.split("/", 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 else ""
    return bucket, key


def _build_s3_public_url(bucket: str, key: str) -> str | None:
    """Construye la URL HTTP pública para un objeto S3."""
    if not bucket or not key:
        return None

    base = settings.S3_PUBLIC_BASE_URL
    if base:
        return f"{base.rstrip('/')}/{key}"

    endpoint = settings.S3_ENDPOINT_URL
    if endpoint:
        endpoint = endpoint.rstrip("/")
        if settings.S3_FORCE_PATH_STYLE:
            return f"{endpoint}/{bucket}/{key}"

        parsed = urlparse(endpoint)
        if parsed.scheme and parsed.netloc:
            host = parsed.netloc
            path = parsed.path.rstrip("/")
            prefix = f"{parsed.scheme}://{bucket}.{host}"
            if path:
                prefix = f"{prefix}{path}"
            return f"{prefix}/{key}"

    region = settings.S3_REGION or "us-east-1"
    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"


def storage_path_to_public_url(path: str | None) -> str | None:
    """Convierte rutas persistidas (locales o S3) en URLs consumibles desde el cliente."""
    if not path:
        return None

    normalized = path.strip()

    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized

    if normalized.startswith("s3://"):
        bucket, key = _parse_s3_path(normalized)
        return _build_s3_public_url(bucket, key)

    web_path = _normalize_local_web_path(normalized)
    if not web_path:
        return None

    base = settings.PUBLIC_BASE_URL
    if not base:
        return web_path

    base = base.rstrip("/")
    if web_path.startswith("/"):
        return f"{base}{web_path}"
    return f"{base}/{web_path}"
