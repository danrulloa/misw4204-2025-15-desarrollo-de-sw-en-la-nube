import os
import logging
import socket
from urllib.parse import urlparse
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor


logger = logging.getLogger("anb.tracing")


def _is_endpoint_reachable(endpoint: str, timeout: float = 0.5) -> bool:
    """Quick TCP reachability check to avoid noisy exporter errors when Tempo is down.

    Supports endpoints like http://host:4318/v1/traces. Only checks host:port.
    """
    try:
        parsed = urlparse(endpoint)
        host = parsed.hostname
        port = parsed.port
        if not host or not port:
            return False
        with socket.create_connection((host, int(port)), timeout=timeout):
            return True
    except Exception:
        return False


def _build_exporter() -> Optional[OTLPSpanExporter]:
    # Prefer explicit traces endpoint, else construct from base endpoint.
    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    endpoint = None
    if traces_endpoint:
        endpoint = traces_endpoint.rstrip("/")
    elif base_endpoint:
        endpoint = base_endpoint.rstrip("/") + "/v1/traces"

    if not endpoint:
        # No endpoint configured -> do not create exporter (no-op)
        logger.warning("OTLP traces endpoint not configured; tracing exporter disabled")
        return None

    # Avoid log spam if Tempo is unreachable: skip exporter when TCP connect fails.
    if not _is_endpoint_reachable(endpoint):
        logger.warning("OTLP endpoint %s not reachable; disabling exporter to keep app healthy", endpoint)
        return None

    # If using HTTP endpoint without TLS, exporter needs insecure=True via env var
    # but HTTP exporter works fine with plain http endpoints by default.
    logger.info("Configuring OTLP HTTP exporter -> %s", endpoint)
    return OTLPSpanExporter(endpoint=endpoint)


def setup_tracing(app: FastAPI, service_name: str = "anb-core") -> None:
    """Configure OpenTelemetry tracing and instrument the FastAPI app.

    Reads configuration from env vars:
      - OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (preferred), e.g. http://tempo:4318/v1/traces
      - OTEL_EXPORTER_OTLP_ENDPOINT (fallback), e.g. http://tempo:4318 (we append /v1/traces)
      - OTEL_SERVICE_NAME (overrides service_name)
    If no endpoint is configured, tracing remains a no-op (app still works).
    """
    svc_name = os.getenv("OTEL_SERVICE_NAME", service_name)

    resource = Resource.create({
        "service.name": svc_name,
        "service.namespace": "anb",
        "service.version": os.getenv("APP_VERSION", "unknown"),
        "deployment.environment": os.getenv("APP_ENV", "production"),
    })

    exporter = _build_exporter()

    # If exporter not configured, keep a basic provider (no processor) so app runs.
    provider = TracerProvider(resource=resource)
    if exporter is not None:
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # Instrument the framework and common clients
    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    # The opentelemetry-instrumentation-asgi package exposes an ASGI middleware
    # named OpenTelemetryMiddleware. Wrap the FastAPI app's ASGI app with it.
    try:
        # Avoid wrapping multiple times in environments where setup_tracing
        # might be called more than once (tests/imports).
        if getattr(app, "asgi_app", None) is not None and not isinstance(
            app.asgi_app, OpenTelemetryMiddleware
        ):
            app.asgi_app = OpenTelemetryMiddleware(app.asgi_app)
    except Exception:
        # If middleware cannot be applied, skip silently to keep app usable
        # (tracing should be best-effort for tests/local runs).
        pass
    HTTPXClientInstrumentor().instrument()
