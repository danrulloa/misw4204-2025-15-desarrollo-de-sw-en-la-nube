"""
Módulo de routers de la API
Contiene todos los endpoints organizados por dominio.
"""

from app.api import videos, public, auth

__all__ = ["videos", "public", "auth"]
