"""No-op tracing module after Tempo rollback."""

def setup_tracing(service_name: str = "anb-worker") -> None:  # type: ignore[unused-argument]
    return
