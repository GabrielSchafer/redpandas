import logging
from typing import Callable, Iterable

from confluent_kafka import Consumer, KafkaError

from ..config import settings
from ..events.envelope import Event
from .serialization import decode

logger = logging.getLogger(__name__)

Handler = Callable[[Event], None]


class EventConsumer:
    def __init__(self, topics: Iterable[str], group_id: str, from_beginning: bool = True) -> None:
        self._topics = list(topics)
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest" if from_beginning else "latest",
                "enable.auto.commit": False,
            }
        )
        self._running = False

    def run(self, handler: Handler) -> None:
        self._consumer.subscribe(self._topics)
        self._running = True
        try:
            while self._running:
                message = self._consumer.poll(1.0)
                if message is None:
                    continue
                if message.error():
                    self._log_error(message.error())
                    continue
                self._dispatch(handler, message)
        finally:
            self._consumer.close()

    def stop(self) -> None:
        self._running = False

    def _dispatch(self, handler: Handler, message) -> None:
        try:
            handler(decode(message.value()))
        except Exception:
            logger.exception("handler failed for offset %s", message.offset())
        else:
            self._consumer.commit(message, asynchronous=False)

    @staticmethod
    def _log_error(error: KafkaError) -> None:
        if not error.retriable():
            logger.error("consumer error: %s", error)
