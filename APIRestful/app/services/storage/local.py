import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import BinaryIO

from app.services.storage.base import StoragePort
from app.config import UPLOAD_DIR
import sys, app
print("app.__file__ =", app.__file__)
print("cwd=", os.getcwd())



def _find_repo_root(start: Path) -> Path:
    """
    Sube directorios hasta hallar un marcador del repo (.git / README.md / requirements.txt).
    Evita que 'app' se resuelva a C:\\app.
    """
    p = start
    markers = {".git", "README.md", "requirements.txt"}
    while True:
        if any((p / m).exists() for m in markers):
            return p
        if p.parent == p:
            # fallback: cwd si no encontramos marcadores
            return Path(os.getcwd()).resolve()
        p = p.parent


class LocalStorageAdapter(StoragePort):
    def __init__(self, base_dir: str | None = None):
        upload_dir = base_dir or UPLOAD_DIR  # "uploads"

        # local.py -> .../app/services/storage/local.py
        repo_root = Path(__file__).resolve().parents[3]  # -> <repo>

        self.base_dir = (repo_root / "storage" / upload_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        day_dir = self.base_dir / datetime.utcnow().strftime("%Y") / datetime.utcnow().strftime("%m") / datetime.utcnow().strftime("%d")
        day_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}-{os.path.basename(filename)}"
        dest_path = (day_dir / safe_name).resolve()

        fileobj.seek(0)
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(fileobj, out)

        if not dest_path.exists() or dest_path.stat().st_size == 0:
            raise RuntimeError(f"No se pudo escribir el archivo en {dest_path}")

        return str(dest_path)