import logging
from typing import Any, Dict


class KeyValueExtraFormatter(logging.Formatter):
    """Formatter that appends LogRecord extras as key=value pairs.

    Only attributes not part of the standard LogRecord fields are included.
    Strings containing spaces or quotes are quoted and escaped.
    """

    # Standard LogRecord attributes to exclude from extras output
    EXCLUDED = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        # Asyncio-specific noisy fields
        "taskName",
        "task",
    }

    def _quote(self, value: Any) -> str:
        # Convert to string safely
        if value is None:
            s = "null"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            s = str(value)

        # Quote strings with spaces or quotes
        if any(ch.isspace() for ch in s) or '"' in s:
            return '"' + s.replace('"', '\\"') + '"'
        return s

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        # Base line similar to default: timestamp level [logger] message
        # time formatting delegated to logging.Formatter
        record.message = record.getMessage()
        base = f"{self.formatTime(record)} {record.levelname} [{record.name}] {record.message}"

        # Collect extras
        extras: Dict[str, Any] = {}
        for k, v in record.__dict__.items():
            if k in self.EXCLUDED or k.startswith("_"):
                continue
            extras[k] = v

        if not extras:
            return base

        extras_str = " ".join(f"{k}={self._quote(v)}" for k, v in extras.items())
        return f"{base} {extras_str}"
