"""
Módulo de routers de la API
Contiene todos los endpoints organizados por dominio.
"""

from app.api import auth, videos, public

__all__ = ["auth", "videos", "public"]
