import os
import uuid
from datetime import datetime
from typing import BinaryIO, Optional

from app.services.storage.base import StoragePort


class S3StorageAdapter(StoragePort):
    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "uploads",
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        force_path_style: bool = False,
        verify_ssl: bool = True,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self.endpoint_url = endpoint_url
        self.force_path_style = force_path_style
        self.verify_ssl = verify_ssl

        # Lazy import to avoid hard dependency when not used
        import boto3  # type: ignore
        from botocore.config import Config  # type: ignore

        config = Config(s3={"addressing_style": "path"} if self.force_path_style else {})
        self._s3 = boto3.client(
            "s3",
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=config,
            verify=self.verify_ssl,
        )

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        today = datetime.utcnow()
        day_dir = f"{today:%Y}/{today:%m}/{today:%d}"
        safe_name = f"{uuid.uuid4().hex}-{os.path.basename(filename)}"
        key = f"{self.prefix}/{day_dir}/{safe_name}"

        fileobj.seek(0)

        # Prefer high-level transfer utility for streaming
        self._s3.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type or "application/octet-stream"},
        )

        # Para mantener compatibilidad con el resto del flujo, devolvemos
        # una ruta lógica con prefijo '/uploads'.
        return f"/{key}"
