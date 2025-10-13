import os, json, pika

VIDEO_EXCHANGE = os.getenv("VIDEO_EXCHANGE", "video")
RABBITMQ_URL  = os.getenv("RABBITMQ_URL")

class RabbitPublisher:
    def __init__(self, url: str | None = None):
        params = pika.URLParameters(url or RABBITMQ_URL)
        self.conn = pika.BlockingConnection(params)
        self.ch = self.conn.channel()
        # El exchange ya existe por definitions.json → usa direct y opcionalmente passive
        self.ch.exchange_declare(
            exchange=VIDEO_EXCHANGE,
            exchange_type="direct",
            durable=True,
            passive=True  # levanta error si NO existe, lo cual te avisa de mala config
        )

    def publish_video(self, payload: dict):
        self.ch.basic_publish(
            exchange=VIDEO_EXCHANGE,
            routing_key="video",  # ← DEBE coincidir con el binding a video_tasks
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistente
            ),
        )

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass