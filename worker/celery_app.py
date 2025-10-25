"""
Compatibility shim to preserve `celery -A celery_app worker` while organizing
the application under app/celery_app.py.
"""

from app.celery_app import app  # re-export for Celery entrypoint

__all__ = ["app"]
