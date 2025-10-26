import os, json, pika
from celery import Celery
from app.config import settings

# ====== LOGGING AÑADIDO ======
import logging
logger = logging.getLogger("anb.rabbit")
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

def _amqp_url() -> str:
    user = os.getenv("RABBITMQ_DEFAULT_USER", "rabbit").strip()
    pwd  = os.getenv("RABBITMQ_DEFAULT_PASS", "rabbitpass").strip()
    # ====== LOGGING AÑADIDO ======
    try:
        logger.info("AMQP creds: user=%s, pass=%s, vhost=/", user, "***")
        logger.info("AMQP URL (masked): amqp://%s:%s@rabbitmq:5672/%%2F", user, "***")
    except Exception:
        pass
    # =================================
    return f"amqp://{user}:{pwd}@rabbitmq:5672/%2F"

class RabbitPublisher:
    def __init__(self):
        params = pika.URLParameters(_amqp_url())
        # timeouts y heartbeat más tolerantes
        params.heartbeat = 30
        params.blocked_connection_timeout = 30

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Creando conexión Pika: heartbeat=%s, blocked_timeout=%s",
                        params.heartbeat, params.blocked_connection_timeout)
        except Exception:
            pass
        # =================================

        self.conn = pika.BlockingConnection(params)

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Conexión Pika establecida: is_open=%s", getattr(self.conn, "is_open", None))
        except Exception:
            pass
        # =================================

        self.ch = self.conn.channel()

        # si el exchange no existe, CREARLO (no uses passive=True)
        self.ch.exchange_declare(
            exchange=settings.VIDEO_EXCHANGE,
            exchange_type="direct",
            durable=True,
            passive=False
        )

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info(
                "Exchange declarado: name=%s, type=%s, durable=%s, passive=%s",
                settings.VIDEO_EXCHANGE, "direct", True, False
            )
        except Exception:
            pass
        # =================================

        # Declarar la cola con los mismos argumentos (DLX) que el worker para
        # evitar errores PRECONDITION_FAILED si otro cliente declaró la cola
        # con esos argumentos.
        try:
            self.ch.queue_declare(
                queue='video_tasks',
                durable=True,
                arguments={
                    'x-dead-letter-exchange': 'video-dlx',
                    'x-dead-letter-routing-key': 'video.dlq'
                }
            )
            # ====== LOGGING AÑADIDO ======
            logger.info(
                "Cola declarada: queue=%s, durable=%s, args=%s",
                'video_tasks', True, {'x-dead-letter-exchange': 'video-dlx', 'x-dead-letter-routing-key': 'video.dlq'}
            )
            # =================================
        except Exception as e:
            # No queremos romper el arranque si la declaración falla; el error
            # original aparecerá en logs si persiste.
            # ====== LOGGING AÑADIDO ======
            try:
                logger.warning("Fallo declarando cola 'video_tasks' (continuando): %s", repr(e))
            except Exception:
                pass
            # =================================
            pass

        # Creación opcional de un cliente Celery ligero para publicar tareas
        # directamente en el broker con el formato que Celery espera.
        broker_url = os.getenv('CELERY_BROKER_URL', _amqp_url())

        # ====== LOGGING AÑADIDO ======
        try:
            logger.info("Celery broker_url (masked if AMQP): %s",
                        broker_url.replace(broker_url.split(':')[1].split('@')[0], "***") if "@" in broker_url else broker_url)
        except Exception:
            pass
        # =================================

        # Crear cliente Celery (debe estar disponible; celery está en requirements)
        self._celery = Celery('api_client', broker=broker_url)

        # Alineamos la configuración del cliente Celery para que no intente
        # declarar la cola con argumentos distintos a los del worker.
        try:
            from kombu import Exchange, Queue
            video_ex = Exchange('video', type='direct', durable=True)
            video_queue = Queue(
                'video_tasks',
                exchange=video_ex,
                routing_key='video',
                durable=True,
                queue_arguments={
                    'x-dead-letter-exchange': 'video-dlx',
                    'x-dead-letter-routing-key': 'video.dlq'
                }
            )
            self._celery.conf.task_queues = (video_queue,)
            self._celery.conf.task_default_queue = 'video_tasks'
            self._celery.conf.task_default_exchange = 'video'
            self._celery.conf.task_default_routing_key = 'video'

            # ====== LOGGING AÑADIDO ======
            try:
                logger.info(
                    "Celery configurado: default_queue=%s, exchange=%s, routing_key=%s",
                    self._celery.conf.task_default_queue,
                    self._celery.conf.task_default_exchange,
                    self._celery.conf.task_default_routing_key
                )
            except Exception:
                pass
            # =================================
        except Exception as e:
            # si kombu no está disponible o falla, no queremos detener el API
            # ====== LOGGING AÑADIDO ======
            try:
                logger.warning("Configuración avanzada de Celery/Kombu no aplicada: %s", repr(e))
            except Exception:
                pass
            # =================================
            pass

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
