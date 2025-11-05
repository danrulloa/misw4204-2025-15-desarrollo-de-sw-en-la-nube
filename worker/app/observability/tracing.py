import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor


def _build_exporter() -> Optional[OTLPSpanExporter]:
    traces_endpoint = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    base_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    endpoint = None
    if traces_endpoint:
        endpoint = traces_endpoint.rstrip("/")
    elif base_endpoint:
        endpoint = base_endpoint.rstrip("/") + "/v1/traces"

    if not endpoint:
        return None

    return OTLPSpanExporter(endpoint=endpoint)


def setup_tracing(service_name: str = "anb-worker") -> None:
    """Configure OpenTelemetry tracing for the worker process and instrument Celery.

    Uses env vars:
      - OTEL_EXPORTER_OTLP_TRACES_ENDPOINT (preferred)
      - OTEL_EXPORTER_OTLP_ENDPOINT (fallback)
      - OTEL_SERVICE_NAME (overrides service_name)
    """
    svc_name = os.getenv("OTEL_SERVICE_NAME", service_name)

    resource = Resource.create({
        "service.name": svc_name,
        "service.namespace": "anb",
        "service.version": os.getenv("APP_VERSION", "unknown"),
        "deployment.environment": os.getenv("APP_ENV", "production"),
    })

    exporter = _build_exporter()

    provider = TracerProvider(resource=resource)
    if exporter is not None:
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)

    # Instrument Celery so each task runs with a span
    CeleryInstrumentor().instrument()
