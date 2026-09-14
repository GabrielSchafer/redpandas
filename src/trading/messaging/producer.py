import logging

from confluent_kafka import Producer

from ..config import settings
from ..events.envelope import Event
from .serialization import encode

logger = logging.getLogger(__name__)


class EventProducer:
    def __init__(self, client_id: str = "trading-producer") -> None:
        self._producer = Producer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
                "client.id": client_id,
                "enable.idempotence": True,
                "acks": "all",
            }
        )

    def publish(self, topic: str, event: Event) -> None:
        self._producer.produce(
            topic=topic,
            key=event.key.encode("utf-8"),
            value=encode(event),
            headers={"event_type": event.type},
            on_delivery=self._on_delivery,
        )
        self._producer.poll(0)

    def flush(self, timeout: float = 5.0) -> None:
        self._producer.flush(timeout)

    @staticmethod
    def _on_delivery(err, msg) -> None:
        if err is not None:
            logger.error("delivery failed on %s: %s", msg.topic(), err)
