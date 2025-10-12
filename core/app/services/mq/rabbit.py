# app/services/mq/rabbit.py
import json, os, pika
VIDEO_EXCHANGE = os.getenv("VIDEO_EXCHANGE", "video")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

class RabbitPublisher:
    def __init__(self, url: str = RABBITMQ_URL):
        params = pika.URLParameters(url)
        self.conn = pika.BlockingConnection(params)
        self.ch = self.conn.channel()
        self.ch.exchange_declare(exchange=VIDEO_EXCHANGE, exchange_type="fanout", durable=True)

    def publish_video(self, payload: dict):
        self.ch.basic_publish(
            exchange=VIDEO_EXCHANGE,
            routing_key="",
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )

    def close(self):
        try: self.conn.close()
        except: pass
