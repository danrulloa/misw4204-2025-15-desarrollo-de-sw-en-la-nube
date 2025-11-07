import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

_io_executor: Optional[ThreadPoolExecutor] = None


def get_io_executor() -> ThreadPoolExecutor:
    """Shared I/O-bound executor for blocking storage operations.

    Sized via env var UPLOAD_IO_MAX_WORKERS (default 32). Keep a single
    process-wide executor to avoid creating many thread pools under load.
    """
    global _io_executor
    if _io_executor is None:
        max_workers = int(os.getenv("UPLOAD_IO_MAX_WORKERS", "32"))
        # Cap to a reasonable upper bound if someone passes a huge number
        max_workers = max(4, min(max_workers, 256))
        _io_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="upload-io")
    return _io_executor
