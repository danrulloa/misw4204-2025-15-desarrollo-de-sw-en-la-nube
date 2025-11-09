from typing import Protocol, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, BackgroundTasks


class UploadServicePort(Protocol):
    async def upload(
        self,
        *,
        user_id: str,
        title: str,
        upload_file: UploadFile,
        user_info: Dict[str, str],
        db: AsyncSession,
        correlation_id: str,
        background_tasks: BackgroundTasks | None,
    ):
        """
        Orquesta la subida de un video y su encolado para procesamiento.

        Debe retornar una tupla (video, correlation_id) donde `video` es la
        instancia persistida del modelo Video y `correlation_id` el identificador
        de la tarea encolada.
        """
        ...

