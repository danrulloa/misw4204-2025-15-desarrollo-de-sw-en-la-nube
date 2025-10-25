from celery import Celery
import logging
import sys
import traceback
import os

from kombu import Exchange, Queue

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


# Subclass Celery to hold shared constants (avoids duplicating literals like 'video.dlq')
class VideoCelery(Celery):
    # Exchanges / routing keys used across the module
    VIDEO_EXCHANGE = 'video'
    VIDEO_DLX_EXCHANGE = 'video-dlx'
    VIDEO_DLQ_ROUTING_KEY = 'video.dlq'
    VIDEO_RETRY_EXCHANGE = 'video-retry'


# Leer broker/backend desde variables de entorno (definen en docker-compose)
BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'amqp://rabbit:rabbitpass@rabbitmq:5672//')
RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'rpc://')

# Instantiate our Celery subclass so we can reference the constants from it
app = VideoCelery('video_worker', broker=BROKER_URL, backend=RESULT_BACKEND)

# Exchanges y colas (coinciden con rabbitmq/definitions.json)
video_ex = Exchange(app.VIDEO_EXCHANGE, type='direct', durable=True)
dlx_ex = Exchange(app.VIDEO_DLX_EXCHANGE, type='direct', durable=True)
retry_ex = Exchange(app.VIDEO_RETRY_EXCHANGE, type='direct', durable=True)

video_queue = Queue(
    'video_tasks',
    exchange=video_ex,
    routing_key='video',
    durable=True,
    queue_arguments={
        'x-dead-letter-exchange': app.VIDEO_DLX_EXCHANGE,
        'x-dead-letter-routing-key': app.VIDEO_DLQ_ROUTING_KEY
    },
)

retry_queue_60s = Queue(
    'video_retry_60s',
    exchange=retry_ex,
    routing_key='video.retry.60',
    durable=True,
    queue_arguments={
        'x-message-ttl': 60000,
        'x-dead-letter-exchange': app.VIDEO_EXCHANGE,
        'x-dead-letter-routing-key': 'video'
    },
)

# dlq queue uses the DLX exchange and the DLQ routing key constant
dlq_queue = Queue('video_dlq', exchange=dlx_ex, routing_key=app.VIDEO_DLQ_ROUTING_KEY, durable=True)

# Configuración de Celery para trabajar con colas durables y reintentos por TTL
app.conf.task_queues = (video_queue, retry_queue_60s, dlq_queue)
app.conf.task_default_queue = 'video_tasks'
app.conf.task_default_exchange = app.VIDEO_EXCHANGE
app.conf.task_default_routing_key = 'video'

app.conf.update(
    task_routes={
        'tasks.process_video.*': {'queue': 'video_tasks'},
    },
    task_acks_late=True,
    worker_prefetch_multiplier=1,
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


# handler para registrar fallos y empujar metadata a la DLQ (informativo)
from celery.signals import task_failure  # noqa: E402
import json  # noqa: E402
from kombu import Connection, Producer  # noqa: E402


@task_failure.connect
def on_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, einfo=None, **kw):
    logger.error(f'Tarea fallida: {sender} id={task_id} exc={exception}')
    try:
        # Publicar metadata en la exchange del DLQ para facilitar inspección (no obligatorio)
        conn = Connection(BROKER_URL)
        with conn:
            producer = Producer(conn)
            payload = json.dumps({
                'task_id': task_id,
                'task_name': getattr(sender, 'name', None),
                'args': args,
                'kwargs': kwargs,
                'exception': str(exception),
            })
            # publicamos directamente a la exchange video-dlx con routing key video.dlq
            producer.publish(payload, exchange=app.VIDEO_DLX_EXCHANGE, routing_key=app.VIDEO_DLQ_ROUTING_KEY, declare=[dlq_queue])
    except Exception as e:
        logger.error(f'No se pudo publicar metadata en DLQ: {e}')
