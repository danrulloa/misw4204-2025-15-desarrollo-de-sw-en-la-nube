import os
import uuid
from datetime import datetime
from typing import BinaryIO, Optional

class S3StorageAdapter:
    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "uploads",
        region: Optional[str] = None,
        endpoint_url: Optional[str] = None,
        force_path_style: bool = False,
        verify_ssl: bool = True,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        self.endpoint_url = endpoint_url
        self.force_path_style = force_path_style
        self.verify_ssl = verify_ssl
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token

        # Lazy import to avoid hard dependency when not used
        import boto3  # type: ignore
        from botocore.config import Config  # type: ignore
        from boto3.s3.transfer import TransferConfig  # type: ignore

        # Fail fast si faltan datos críticos
        missing = []
        if not self.bucket:
            missing.append("S3 bucket")
        if not self.region:
            missing.append("S3 region")
        if not self.access_key_id:
            missing.append("AWS_ACCESS_KEY_ID")
        if not self.secret_access_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if missing:
            raise RuntimeError(f"Configuración S3/AWS incompleta: falta(n) {', '.join(missing)}")

        # Tune botocore connection pool and transfer concurrency for higher throughput
        max_pool = int(os.getenv("S3_MAX_POOL_CONNECTIONS", "50"))
        transfer_concurrency = int(os.getenv("S3_TRANSFER_MAX_CONCURRENCY", "8"))

        config = Config(
            s3={"addressing_style": "path"} if self.force_path_style else {},
            retries={"max_attempts": 3},
            max_pool_connections=max_pool,
        )
        # Crear cliente con credenciales explícitas (sin cadena de proveedores)
        self._s3 = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.region,
            endpoint_url=self.endpoint_url,
            config=config,
            verify=self.verify_ssl,
        )
        # Configure multipart uploads (boto3 uses its own internal threads per transfer)
        self._transfer_cfg = TransferConfig(
            max_concurrency=transfer_concurrency,
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )

    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        today = datetime.utcnow()
        day_dir = f"{today:%Y}/{today:%m}/{today:%d}"
        safe_name = f"{uuid.uuid4().hex}-{os.path.basename(filename)}"
        key = f"{self.prefix}/{day_dir}/{safe_name}"

        fileobj.seek(0)

        # Prefer high-level transfer utility for streaming (sync)
        self._s3.upload_fileobj(
            Fileobj=fileobj,
            Bucket=self.bucket,
            Key=key,
            ExtraArgs={"ContentType": content_type or "application/octet-stream"},
            Config=self._transfer_cfg,
        )

        # Para mantener compatibilidad con el resto del flujo, devolvemos
        # una ruta lógica con prefijo '/uploads'.
        return f"/{key}"

    # Nota: ruta única optimizada -> save() síncrono con boto3; no se expone variante async.
