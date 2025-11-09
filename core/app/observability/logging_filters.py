import logging
import re
from typing import Iterable, List


class ExcludePathsFilter(logging.Filter):
    """Filter that excludes uvicorn.access logs matching request paths.

    Works with uvicorn which logs access via logger "uvicorn.access" and sets
    extra fields like request_line and status_code. We inspect either the
    request_line or the formatted message as a fallback.
    """

    def __init__(self, patterns: Iterable[str]) -> None:
        super().__init__()
        self._regexes: List[re.Pattern[str]] = [re.compile(p) for p in patterns]

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore[override]
        # Prefer uvicorn's structured field if present
        text = getattr(record, "request_line", None)
        if not text:
            # Fallback to formatted message contents
            try:
                text = record.getMessage()
            except Exception:
                text = str(record.msg)
        if not isinstance(text, str):
            text = str(text)

        for regex in self._regexes:
            if regex.search(text):
                return False
        return True


def install_uvicorn_access_filter() -> None:
    """Install an access-log filter to hide /health and /metrics lines.

    This keeps other access logs untouched.
    """
    logger = logging.getLogger("uvicorn.access")
    # Avoid duplicating filters if reloaded
    for f in list(logger.filters):
        if isinstance(f, ExcludePathsFilter):
            logger.removeFilter(f)
    logger.addFilter(ExcludePathsFilter(patterns=[r"\s/health\s", r"\s/metrics\s"]))
