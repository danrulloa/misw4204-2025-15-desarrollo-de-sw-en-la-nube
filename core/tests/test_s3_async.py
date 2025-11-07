from app.services.storage.s3 import S3StorageAdapter


def test_s3_adapter_exposes_sync_save_only():
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

    # Debe existir solo el método síncrono 'save' (sin variantes async)
    assert hasattr(s3, "save")
    assert not hasattr(s3, "save_async")
    assert not hasattr(s3, "save_async_compat")

