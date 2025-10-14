
import os, uuid, shutil
from pathlib import Path
from datetime import datetime
from typing import BinaryIO
from app.services.storage.base import StoragePort
from app.config import UPLOAD_DIR

class LocalStorageAdapter(StoragePort):
    def __init__(self, base_dir: str | None = None):
        upload_dir = base_dir or UPLOAD_DIR
        repo_root = Path(__file__).resolve().parents[3]          # <repo>
        self.abs_root = (repo_root / "storage").resolve()        # .../core/storage
        self.base_dir = (self.abs_root / upload_dir).resolve()   # .../storage/uploads
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        today = datetime.utcnow()
        day_dir = self.base_dir / f"{today:%Y}" / f"{today:%m}" / f"{today:%d}"
        day_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}-{os.path.basename(filename)}"
        dest_path = (day_dir / safe_name).resolve()

        fileobj.seek(0)
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(fileobj, out)

        # Devolver ruta **relativa** (desde /storage), ej: /uploads/2025/10/13/uuid.mp4
        rel_from_storage = dest_path.relative_to(self.abs_root).as_posix()
        return f"/{rel_from_storage}"