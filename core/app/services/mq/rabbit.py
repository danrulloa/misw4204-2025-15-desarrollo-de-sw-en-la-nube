import os, json, pika
from app.config import settings

def _amqp_url() -> str:
    user = os.getenv("RABBITMQ_DEFAULT_USER", "rabbit").strip()
    pwd  = os.getenv("RABBITMQ_DEFAULT_PASS", "rabbitpass").strip()
    # especifica VHOST "/" explícito como %2F
    return f"amqp://{user}:{pwd}@rabbitmq:5672/%2F"

class RabbitPublisher:
    def __init__(self):
        params = pika.URLParameters(_amqp_url())
        # timeouts y heartbeat más tolerantes
        params.heartbeat = 30
        params.blocked_connection_timeout = 30
        self.conn = pika.BlockingConnection(params)
        self.ch = self.conn.channel()
        # si el exchange no existe, CREARLO (no uses passive=True)
        self.ch.exchange_declare(
            exchange=settings.VIDEO_EXCHANGE,
            exchange_type="direct",
            durable=True,
            passive=False
        )

    def publish_video(self, payload: dict):
        self.ch.basic_publish(
            exchange=settings.VIDEO_EXCHANGE,
            routing_key="video",
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
            ),
            mandatory=False,
        )

    def close(self):
        try: self.conn.close()
        except Exception: pass
