"""Deprecated: Local storage adapter removed in favor of S3-only backend.

This module is intentionally empty and will raise on import to prevent usage.
"""

raise ImportError(
    "LocalStorageAdapter has been removed. Use the S3 adapter via "
    "app.services.uploads.local.STORAGE instead."
)