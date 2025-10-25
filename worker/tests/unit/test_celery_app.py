import importlib
import json
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
    # Provide required env to allow import
    mod = reload_module(
        monkeypatch,
        CELERY_BROKER_URL='amqp://user:pass@host:5672/vhost',
        CELERY_RESULT_BACKEND='rpc://',
    )

    # Check default queue/exchange/routing key
    assert mod.app.conf.task_default_queue == 'video_tasks'
    assert mod.app.conf.task_default_exchange == 'video'
    assert mod.app.conf.task_default_routing_key == 'video'

    # task_routes contains wildcard for process_video tasks
    routes = mod.app.conf.task_routes or {}
    assert 'tasks.process_video.*' in routes
    assert routes['tasks.process_video.*']['queue'] == 'video_tasks'

    # There should be three queues configured with expected names and properties
    queues = list(mod.app.conf.task_queues)
    names = {q.name for q in queues}
    assert {'video_tasks', 'video_retry_60s', 'video_dlq'} <= names

    def get_queue(n):
        return next(q for q in queues if q.name == n)

    video_q = get_queue('video_tasks')
    assert video_q.exchange.name == 'video'
    assert video_q.routing_key == 'video'
    assert video_q.durable is True
    assert video_q.queue_arguments.get('x-dead-letter-exchange') == 'video-dlx'
    assert video_q.queue_arguments.get('x-dead-letter-routing-key') == 'video.dlq'

    retry_q = get_queue('video_retry_60s')
    assert retry_q.exchange.name == 'video-retry'
    assert retry_q.routing_key == 'video.retry.60'
    assert retry_q.durable is True
    assert retry_q.queue_arguments.get('x-message-ttl') == 60000
    assert retry_q.queue_arguments.get('x-dead-letter-exchange') == 'video'
    assert retry_q.queue_arguments.get('x-dead-letter-routing-key') == 'video'

    dlq_q = get_queue('video_dlq')
    assert dlq_q.exchange.name == 'video-dlx'
    assert dlq_q.routing_key == 'video.dlq'
    assert dlq_q.durable is True


def test_task_failure_publishes_to_dlx(monkeypatch):
    # Reload to get a clean module namespace with required env
    mod = reload_module(
        monkeypatch,
        CELERY_BROKER_URL='amqp://user:pass@host:5672/vhost',
        CELERY_RESULT_BACKEND='rpc://',
    )

    # Patch Connection and Producer in the module namespace
    with mock.patch.object(mod, 'Connection') as MockConn, mock.patch.object(mod, 'Producer') as MockProducer:
        # make Connection a context manager
        conn_instance = MockConn.return_value
        conn_instance.__enter__.return_value = conn_instance
        conn_instance.__exit__.return_value = False

        producer_instance = MockProducer.return_value

        # Call the signal handler directly
        class S:
            name = 'dummy.task'
        exc = RuntimeError('boom')
        mod.on_task_failure(sender=S(), task_id='abc123', exception=exc, args=['x'], kwargs={'y': 1})

        # Producer should be constructed with the connection
        MockProducer.assert_called_once_with(conn_instance)
        # And publish should be called once with expected routing
        assert producer_instance.publish.called
        call = producer_instance.publish.call_args
        # payload is first positional arg, JSON string
        payload = call.args[0]
        data = json.loads(payload)
        assert data['task_id'] == 'abc123'
        assert data['task_name'] == 'dummy.task'
        assert data['args'] == ['x']
        assert data['kwargs'] == {'y': 1}
        assert 'boom' in data['exception']

        # Check kwargs for routing to DLX
        kwargs = call.kwargs
        assert kwargs['exchange'] == 'video-dlx'
        assert kwargs['routing_key'] == 'video.dlq'
        # declare should include the DLQ queue
        declare = kwargs.get('declare')
        assert isinstance(declare, (list, tuple)) and len(declare) == 1
        # We can't compare the Queue objects directly across reloads, so check name
        assert getattr(declare[0], 'name', None) == 'video_dlq'
