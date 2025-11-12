from app.services.mq.celery_pool import get_pool

import logging
logger = logging.getLogger("anb.publisher")

class QueuePublisher:
    """Publicador de tareas de procesamiento de video usando Celery sobre SQS.

    Sustituye al antiguo RabbitPublisher eliminando dependencias de AMQP
    (exchanges/routing keys). Solo envía a la cola default configurada.
    """
    def __init__(self):
        pool = get_pool()
        self._celery = pool.get_client()
        logger.info("QueuePublisher usa Celery pool singleton")

    def publish_video(self, payload: dict):
        """Publicar la tarea de procesamiento de video.

        Espera un dict con al menos `input_path`. Opcionalmente `video_id` y
        `correlation_id`. Construye los args posicionales de la task
        `tasks.process_video.run` en orden: [video_id?, input_path, correlation_id?].
        """
        input_path = None
        if isinstance(payload, dict):
            input_path = payload.get('input_path') or payload.get('video_path') or payload.get('path')
        if not input_path:
            raise ValueError('publish_video expects payload dict containing input_path')

        headers = {}
        if isinstance(payload, dict) and 'correlation_id' in payload:
            headers['correlation_id'] = payload.get('correlation_id')

        args_list = []
        if isinstance(payload, dict) and 'video_id' in payload:
            args_list.append(payload.get('video_id'))
        args_list.append(input_path)
        if isinstance(payload, dict) and 'correlation_id' in payload:
            args_list.append(payload.get('correlation_id'))

        self._celery.send_task(
            'tasks.process_video.run',
            args=args_list,
            kwargs={},
            queue='video_tasks',  # debe coincidir con SQS_QUEUE_NAME
            serializer='json',
            headers=headers or None,
        )

    def close(self):
        # No hay conexión directa que cerrar; mantenido por compatibilidad
        return
