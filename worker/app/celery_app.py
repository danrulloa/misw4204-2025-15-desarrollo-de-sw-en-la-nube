from celery import Celery
import logging
import sys
import traceback
import os
import time

# Prometheus metrics (export to /metrics via start_http_server)
try:
    from prometheus_client import Counter, Histogram, start_http_server
    _PROM_AVAILABLE = True
except Exception:
    _PROM_AVAILABLE = False

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Tracing removido (Tempo rollback)


# Subclass Celery to hold shared constants (avoids duplicating literals like 'video.dlq')
class VideoCelery(Celery):
    """Celery subclass (reservado por si se requiere extender en el futuro)."""
    pass


BROKER_URL_RAW = os.getenv('CELERY_BROKER_URL', 'sqs://').strip() or 'sqs://'
# Normalizar broker (quitar query ?region= us-east-1 si quedó de configuraciones anteriores)
if BROKER_URL_RAW.startswith('sqs://') and '?region=' in BROKER_URL_RAW:
    BROKER_URL_RAW = 'sqs://'
BROKER_URL = BROKER_URL_RAW
RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'rpc://')

# Instantiate our Celery subclass so we can reference the constants from it
app = VideoCelery('video_worker', broker=BROKER_URL, backend=RESULT_BACKEND)

QUEUE_NAME = os.getenv('SQS_QUEUE_NAME', 'video_tasks')

# Configuración mínima para SQS (sin exchanges/routing AMQP)
app.conf.task_default_queue = QUEUE_NAME
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True

region = os.getenv('AWS_REGION', 'us-east-1')
visibility_timeout = int(os.getenv('SQS_VISIBILITY_TIMEOUT', '60'))
wait_time_seconds = int(os.getenv('SQS_WAIT_TIME_SECONDS', '20'))
app.conf.broker_transport_options = {
    'region': region,
    'visibility_timeout': visibility_timeout,
    'wait_time_seconds': wait_time_seconds,
}

app.conf.update(
    task_routes={'tasks.process_video.*': {'queue': QUEUE_NAME}},
    result_expires=3600,
)

# Intentamos importar explícitamente las tareas para exponer errores lo antes posible
try:
    logger.info('Intentando importar tasks.process_video para validar imports de tareas...')
    import tasks.process_video  # noqa: F401
    logger.info('Importación de tasks.process_video OK')
except Exception:
    logger.error('Error al importar tasks.process_video. Traza:')
    traceback.print_exc()
    # Re-raise para que el proceso falle y el log muestre la causa original
    raise

try:
    app.autodiscover_tasks(['tasks'])
    logger.info('Auto-discovery de tareas completado correctamente')
except Exception:
    logger.error('autodiscover_tasks falló. Traza:')
    traceback.print_exc()
    raise

# ---------------------------
# Prometheus metrics exporter
# ---------------------------
_task_starts = {}
if _PROM_AVAILABLE:
    # Guardar los nombres base que podrían haber sido registrados por reloads/tests
    try:
        from prometheus_client import REGISTRY

        def _get_existing_collector(candidates):
            for n in candidates:
                if n in REGISTRY._names_to_collectors:
                    return REGISTRY._names_to_collectors[n]
            return None

        # Try to reuse an already-registered Counter to avoid ValueError on module reload
        TASKS_PROCESSED = _get_existing_collector([
            'anb_worker_tasks',
            'anb_worker_tasks_total',
            'anb_worker_tasks_created',
        ]) or Counter(
            'anb_worker_tasks',
            'Number of worker tasks processed',
            ['task_name', 'status'],
        )

        # Same for duration histogram
        TASK_DURATION = _get_existing_collector([
            'anb_worker_task_duration_seconds',
        ]) or Histogram(
            'anb_worker_task_duration_seconds', 'Duración de tareas en segundos', ['task_name']
        )
    except Exception:
        # Fallback defensivo: attempt creation and swallow duplicate registration errors
        try:
            TASKS_PROCESSED = Counter(
                'anb_worker_tasks',
                'Number of worker tasks processed',
                ['task_name', 'status'],
            )
        except Exception:
            TASKS_PROCESSED = None
        try:
            TASK_DURATION = Histogram(
                'anb_worker_task_duration_seconds', 'Duración de tareas en segundos', ['task_name']
            )
        except Exception:
            TASK_DURATION = None

    # Inicia el servidor de métricas solo una vez (padre) para evitar conflictos de puerto
    try:
        if not os.environ.get('ANB_METRICS_STARTED'):
            port = int(os.environ.get('WORKER_METRICS_PORT', '9100'))
            start_http_server(port)
            os.environ['ANB_METRICS_STARTED'] = '1'
            logger.info('Prometheus metrics server iniciado en puerto %s', port)
    except Exception:
        logger.exception('No se pudo iniciar el servidor de métricas Prometheus')


# handler para registrar fallos y empujar metadata a la DLQ (informativo)
from celery.signals import task_failure  # noqa: E402
import json  # noqa: E402
from celery.signals import task_prerun, task_postrun  # noqa: E402


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, einfo=None, **kw):
    logger.error(f'Tarea fallida: {sender} id={task_id} exc={exception}')
    # Métricas
    try:
        if _PROM_AVAILABLE:
            TASKS_PROCESSED.labels(task_name=getattr(sender, 'name', 'unknown'), status='failure').inc()
    except Exception:
        pass
    # Con SQS puro no replicamos DLQ publish manual (la política redrive maneja fallos).
    pass


@task_prerun.connect
def on_task_prerun(task_id=None, task=None, *args, **kwargs):
    try:
        _task_starts[task_id] = time.time()
    except Exception:
        pass


@task_postrun.connect
def on_task_postrun(task_id=None, task=None, retval=None, state=None, **kwargs):
    try:
        name = getattr(task, 'name', 'unknown')
        if _PROM_AVAILABLE:
            TASKS_PROCESSED.labels(task_name=name, status='success' if state == 'SUCCESS' else str(state or 'unknown')).inc()
            start_t = _task_starts.pop(task_id, None)
            if start_t:
                TASK_DURATION.labels(task_name=name).observe(max(0.0, time.time() - start_t))
    except Exception:
        pass
