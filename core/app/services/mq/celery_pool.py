"""Singleton de cliente Celery para publicar tareas a SQS.

El cambio de RabbitMQ a SQS elimina la necesidad de declarar exchanges,
routing keys y argumentos avanzados de cola. Con el transport SQS de Celery
solo necesitamos:
 - broker URL (sqs://)
 - región (env AWS_REGION)
 - nombre de la cola (env SQS_QUEUE_NAME)

Este módulo expone un pool para reutilizar la conexión Celery y evitar
re-crearla por cada publicación.
"""

import os
import logging
from typing import Optional
from celery import Celery

logger = logging.getLogger("anb.celery_pool")


def _broker_url() -> str:
    """Devuelve broker URL normalizado (sin query ?region=...).

    La región debe ir en broker_transport_options, no embebida en la URL, porque
    Celery/kombu no acepta 'region' como parámetro de Connection._init_params.
    """
    raw = os.getenv("CELERY_BROKER_URL", "sqs://").strip() or "sqs://"
    # Limpiar patrones antiguos como sqs://?region=us-east-1
    if raw.startswith("sqs://") and "?region=" in raw:
        raw = "sqs://"
    return raw


def _queue_name() -> str:
    q = os.getenv("SQS_QUEUE_NAME", "video_tasks").strip()
    if not q:
        raise RuntimeError("SQS_QUEUE_NAME vacío: nombre de cola requerido")
    return q


class CeleryPool:
    _instance: Optional['CeleryPool'] = None
    _celery_app: Optional[Celery] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_celery()
        return cls._instance

    def _initialize_celery(self):
        if self._celery_app is not None:
            return
        broker_url = _broker_url()
        queue_name = _queue_name()
        region = os.getenv("AWS_REGION", "us-east-1").strip() or "us-east-1"
        backend = os.getenv("CELERY_RESULT_BACKEND", "rpc://").strip() or "rpc://"

        logger.info(
            "Inicializando cliente Celery singleton (SQS) broker=%s queue=%s region=%s",
            broker_url, queue_name, region
        )
        app = Celery('api_client', broker=broker_url, backend=backend)

        # Transport options específicos para SQS (region aquí, NO en la URL)
        app.conf.broker_transport_options = {
            'region': region,
            'visibility_timeout': int(os.getenv('SQS_VISIBILITY_TIMEOUT', '60')),
            'wait_time_seconds': int(os.getenv('SQS_WAIT_TIME_SECONDS', '20')),
        }
        app.conf.task_default_queue = queue_name
        app.conf.worker_prefetch_multiplier = 1  # Prefetch 1 evita retener mensajes invisibles largos
        app.conf.task_acks_late = True
        app.conf.task_reject_on_worker_lost = True

        self._celery_app = app
        logger.info("Cliente Celery SQS listo")

    def get_client(self) -> Celery:
        assert self._celery_app is not None
        return self._celery_app


_pool: Optional[CeleryPool] = None


def get_pool() -> CeleryPool:
    global _pool
    if _pool is None:
        _pool = CeleryPool()
    return _pool
