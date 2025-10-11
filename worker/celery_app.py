from celery import Celery
import logging
import sys
import traceback

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


app = Celery(
    'video_worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

app.conf.update(
    task_routes={
        'tasks.process_video.*': {'queue': 'video_queue'},
    },
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
