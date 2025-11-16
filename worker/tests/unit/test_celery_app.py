import importlib
import os
import sys
from unittest import mock

import pytest


# Skip this suite entirely if celery isn't installed in the local environment
pytest.importorskip("celery")

MODULE_NAME = 'app.celery_app'


def reload_module(monkeypatch, **env):
    """Reload app.celery_app with specific env vars set.
    Returns the imported module.
    """
    # Apply env vars for this reload
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    # Ensure a clean import
    if MODULE_NAME in sys.modules:
        del sys.modules[MODULE_NAME]
    mod = importlib.import_module(MODULE_NAME)
    return mod


def test_env_broker_and_backend_applied(monkeypatch):
    broker = 'amqp://user:pass@host:5672/vhost'
    backend = 'rpc://'
    mod = reload_module(monkeypatch, CELERY_BROKER_URL=broker, CELERY_RESULT_BACKEND=backend)

    # Celery stores these in app.conf
    assert mod.app.conf.broker_url == broker
    assert mod.app.conf.result_backend == backend


def test_task_queues_and_routes_config(monkeypatch):
    # Provide required env to allow import con la configuración SQS actual
    mod = reload_module(
        monkeypatch,
        CELERY_BROKER_URL='sqs://',
        CELERY_RESULT_BACKEND='rpc://',
        SQS_QUEUE_NAME='video_tasks',
        AWS_REGION='us-east-1',
        SQS_VISIBILITY_TIMEOUT='45',
        SQS_WAIT_TIME_SECONDS='15',
    )

    # Confirmamos que el módulo lea correctamente la cola objetivo
    assert mod.QUEUE_NAME == 'video_tasks'

    routes = mod.app.conf.task_routes or {}
    assert routes == {'tasks.process_video.*': {'queue': 'video_tasks'}}

    # Configuración básica del worker debe permanecer
    assert mod.app.conf.worker_prefetch_multiplier == 1
    assert mod.app.conf.task_acks_late is True
    assert mod.app.conf.worker_hijack_root_logger is False

    opts = mod.app.conf.broker_transport_options
    assert opts['region'] == 'us-east-1'
    assert opts['visibility_timeout'] == 45
    assert opts['wait_time_seconds'] == 15


def test_task_failure_updates_metrics(monkeypatch):
    # Reload to get a clean module namespace with required env
    mod = reload_module(
        monkeypatch,
        CELERY_BROKER_URL='sqs://',
        CELERY_RESULT_BACKEND='rpc://',
    )

    # Forzar disponibilidad de métricas y proveer un mock simple
    mod._PROM_AVAILABLE = True

    counter_mock = mock.Mock()
    labels_mock = mock.Mock()
    counter_mock.labels.return_value = labels_mock
    mod.TASKS_PROCESSED = counter_mock

    class DummyTask:
        name = 'dummy.task'

    exc = RuntimeError('boom')
    mod.on_task_failure(sender=DummyTask(), task_id='abc123', exception=exc, args=['x'], kwargs={'y': 1})

    counter_mock.labels.assert_called_once_with(task_name='dummy.task', status='failure')
    labels_mock.inc.assert_called_once_with()
