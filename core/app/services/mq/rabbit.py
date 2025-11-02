from app.services.mq.celery_pool import get_pool

import logging
logger = logging.getLogger("anb.rabbit")

class RabbitPublisher:
    def __init__(self):
        # Usar pool singleton de Celery en lugar de crear cliente nuevo
        pool = get_pool()
        self._celery = pool.get_client()
        logger.info("RabbitPublisher usa Celery pool singleton")

    def publish_video(self, payload: dict):
        """Publish a video processing task. Backwards-compatible signature:

        - If `payload` is a dict with an `input_path` key, we will send a Celery
          task `tasks.process_video.run` with that path as the single arg.
        - Uses Celery's send_task so workers accept the message.
        """
        # Enforce Celery usage: always send a Celery task so workers can process it.

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("publish_video() payload keys=%s", list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__)
        except Exception:
            pass
        # =================================

        # Extract input_path from payload if possible, otherwise expect full payload
        input_path = None
        if isinstance(payload, dict):
            input_path = payload.get('input_path') or payload.get('video_path') or payload.get('path')

        if not input_path:
            # ====== LOGGING AÑADIDO ======
            try:
                logger.error("publish_video() sin input_path en payload: %s", payload)
            except Exception:
                pass
            # =================================
            raise ValueError('publish_video expects payload dict containing input_path')

        headers = {}
        if isinstance(payload, dict) and 'correlation_id' in payload:
            headers['correlation_id'] = payload.get('correlation_id')

        # Build positional args for the task: (video_id?, input_path, correlation_id?)
        args_list = []
        if isinstance(payload, dict) and 'video_id' in payload:
            args_list.append(payload.get('video_id'))
        # input_path is required
        args_list.append(input_path)
        if isinstance(payload, dict) and 'correlation_id' in payload:
            args_list.append(payload.get('correlation_id'))

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info(
                "Enviando tarea Celery: task=%s, args=%s, headers=%s, queue=%s, routing_key=%s, serializer=%s",
                'tasks.process_video.run', args_list, headers or None, 'video_tasks', 'video', 'json'
            )
        except Exception:
            pass
        # =================================

        # Use Celery send_task to ensure worker recognizes the message
        self._celery.send_task(
            'tasks.process_video.run',
            args=args_list,
            kwargs={},
            queue='video_tasks',
            routing_key='video',
            serializer='json',
            headers=headers or None,
        )

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Tarea Celery enviada correctamente.")
        except Exception:
            pass
        # =================================

    # publish_video_task removed: single canonical publish_video method is used

    def close(self):
        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Cerrando conexión Pika...")
        except Exception:
            pass
        # =================================
        try: self.conn.close()
        except Exception: pass
        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Conexión cerrada.")
        except Exception:
            pass
        # =================================
