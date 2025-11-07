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
        from botocore.exceptions import NoCredentialsError  # type: ignore

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

        config = Config(s3={"addressing_style": "path"} if self.force_path_style else {})
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
        )

        # Para mantener compatibilidad con el resto del flujo, devolvemos
        # una ruta lógica con prefijo '/uploads'.
        return f"/{key}"

    async def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:  # async compatible alias
        """Async-compatible save method: delegates to save_async.

        Having `save` as an async function allows callers that inspect for an
        async `save` to await it directly. Internally we still lazy-import
        aioboto3 in `save_async`.
        """
        return await self.save_async(fileobj, filename, content_type)

    async def save_async(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        """Async save using aioboto3. Kept as `save_async` to avoid changing public sync API.

        This method is lazy-imported to avoid requiring aioboto3 unless the async path is used.
        """
        # Lazy import aioboto3 to avoid adding runtime penalty when not used
        try:
            import aioboto3  # type: ignore
        except Exception as e:
            raise RuntimeError("aioboto3 is required for async S3 operations") from e

        today = datetime.utcnow()
        day_dir = f"{today:%Y}/{today:%m}/{today:%d}"
        safe_name = f"{uuid.uuid4().hex}-{os.path.basename(filename)}"
        key = f"{self.prefix}/{day_dir}/{safe_name}"

        # Reset to start
        try:
            fileobj.seek(0)
        except Exception:
            pass

        session = aioboto3.Session()
        # Create client with same credentials
        async with session.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.region,
            endpoint_url=self.endpoint_url,
        ) as s3:
            # aioboto3's upload_fileobj is async
            await s3.upload_fileobj(
                Fileobj=fileobj,
                Bucket=self.bucket,
                Key=key,
                ExtraArgs={"ContentType": content_type or "application/octet-stream"},
            )

        return f"/{key}"

    # Backwards compatible alias name used by some callers
    async def save_async_compat(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        return await self.save_async(fileobj, filename, content_type)
