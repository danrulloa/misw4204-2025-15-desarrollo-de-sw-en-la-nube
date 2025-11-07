import pytest
import io

from app.services.storage.s3 import S3StorageAdapter


@pytest.mark.asyncio
async def test_s3_save_async_requires_aioboto3():
    # Construir adaptador con parámetros mínimos para evitar RuntimeError en init
    s3 = S3StorageAdapter(
        bucket="dummy-bucket",
        prefix="uploads",
        region="us-east-1",
        endpoint_url=None,
        force_path_style=False,
        verify_ssl=True,
        access_key_id="AKIAFAKE",
        secret_access_key="FAKESECRET",
        session_token=None,
    )

    # Llamar save_async debe intentar importar aioboto3 y lanzar RuntimeError si no está instalado
    with pytest.raises(RuntimeError) as exc:
        await s3.save_async(io.BytesIO(b"x"), "file.mp4", "video/mp4")
    assert "aioboto3" in str(exc.value)


@pytest.mark.asyncio
async def test_s3_save_async_compat_alias():
    s3 = S3StorageAdapter(
        bucket="dummy-bucket",
        prefix="uploads",
        region="us-east-1",
        endpoint_url=None,
        force_path_style=False,
        verify_ssl=True,
        access_key_id="AKIAFAKE",
        secret_access_key="FAKESECRET",
        session_token=None,
    )

    with pytest.raises(RuntimeError):
        await s3.save_async_compat(io.BytesIO(b"x"), "file.mp4", "video/mp4")

