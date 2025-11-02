"""Pool singleton de cliente Celery reutilizable."""

import os
import logging
from celery import Celery
from kombu import Exchange, Queue

logger = logging.getLogger("anb.celery_pool")


def _amqp_url() -> str:
    """Build the AMQP URL strictly from environment."""
    url_from_env = os.getenv("RABBITMQ_URL")
    if url_from_env and url_from_env.strip():
        return url_from_env.strip()
    
    # Fall back to CELERY_BROKER_URL
    broker_url = os.getenv('CELERY_BROKER_URL')
    if broker_url:
        return broker_url
    
    raise RuntimeError("Neither RABBITMQ_URL nor CELERY_BROKER_URL is set")


class CeleryPool:
    """Pool singleton de cliente Celery reutilizable."""
    
    _instance: 'CeleryPool' = None
    _celery_app: Celery = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_celery()
        return cls._instance
    
    def _initialize_celery(self):
        """Inicializar cliente Celery una sola vez."""
        if self._celery_app is not None:
            return
        
        broker_url = _amqp_url()
        logger.info("Inicializando cliente Celery singleton (pool)")
        
        self._celery_app = Celery('api_client', broker=broker_url)
        
        # Configurar colas como en el worker
        try:
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
            self._celery_app.conf.task_queues = (video_queue,)
            self._celery_app.conf.task_default_queue = 'video_tasks'
            self._celery_app.conf.task_default_exchange = 'video'
            self._celery_app.conf.task_default_routing_key = 'video'
            logger.info("Cliente Celery configurado (pool)")
        except Exception as e:
            logger.warning("Configuración avanzada de Celery falló: %s", e)
    
    def get_client(self) -> Celery:
        """Obtener cliente Celery singleton."""
        return self._celery_app


_pool: CeleryPool = None


def get_pool() -> CeleryPool:
    """Obtener singleton del pool Celery."""
    global _pool
    if _pool is None:
        _pool = CeleryPool()
    return _pool

