# Puerto/Interfaz: define qué operaciones ofrece el almacenamiento
from typing import Protocol, BinaryIO

class StoragePort(Protocol):
    def save(self, fileobj: BinaryIO, filename: str, content_type: str) -> str:
        """Guarda el fileobj con el nombre dado y retorna la ruta/URL resultante."""
        ...