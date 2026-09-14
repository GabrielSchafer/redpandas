import logging
import signal
from typing import Any

from ..events.envelope import Event
from ..messaging.consumer import EventConsumer
from ..messaging.producer import EventProducer
from ..messaging.router import Router

logger = logging.getLogger(__name__)


class Worker:
    name: str = "worker"
    topics: list[str] = []

    def __init__(self) -> None:
        self.producer = EventProducer(client_id=self.name)
        self.consumer = EventConsumer(self.topics, group_id=f"{self.name}-group")
        self.router = Router()
        self.register()

    def register(self) -> None:
        raise NotImplementedError

    def emit(self, topic: str, event_type: str, key: str, payload: dict[str, Any], source: Event | None = None) -> None:
        correlation_id = source.correlation_id or source.event_id if source else None
        self.producer.publish(topic, Event(type=event_type, key=key, payload=payload, correlation_id=correlation_id))

    def run(self) -> None:
        signal.signal(signal.SIGINT, lambda *_: self.consumer.stop())
        signal.signal(signal.SIGTERM, lambda *_: self.consumer.stop())
        logger.info("%s listening on %s", self.name, ", ".join(self.topics))
        self.consumer.run(self._handle)
        self.producer.flush()

    def _handle(self, event: Event) -> None:
        self.router.dispatch(event)
        self.producer.flush(1.0)
