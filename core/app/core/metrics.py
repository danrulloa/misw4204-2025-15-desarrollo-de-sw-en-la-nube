from prometheus_client import Histogram
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Buckets extended up to 120s to capture long uploads
HISTOGRAM_BUCKETS = [
    0.001, 0.005, 0.01, 0.025, 0.05,
    0.1, 0.25, 0.5, 1, 2.5,
    5, 10, 30, 60, 120,
]

REQUEST_HISTOGRAM = Histogram(
    'http_request_duration_seconds_handler',
    'HTTP request latency by handler (custom, extended buckets)',
    ['handler', 'method', 'status'],
    buckets=HISTOGRAM_BUCKETS,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        try:
            handler = request.url.path
        except Exception:
            handler = request.scope.get('path', 'unknown')
        method = request.method
        status = str(response.status_code)
        try:
            REQUEST_HISTOGRAM.labels(handler=handler, method=method, status=status).observe(duration)
        except Exception:
            # avoid breaking app if prometheus client errors
            pass
        return response
