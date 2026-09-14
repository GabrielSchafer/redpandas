import logging
from threading import Thread
from uuid import uuid4

from ..events.topics import Topic
from ..messaging.consumer import EventConsumer
from ..store.projections import Projection

logger = logging.getLogger(__name__)

PROJECTION_TOPICS = [Topic.ACCOUNT_EVENTS, Topic.ORDER_EVENTS, Topic.TRADE_EVENTS, Topic.LEDGER_EVENTS]


class ProjectionStream:
    def __init__(self) -> None:
        self.projection = Projection()
        self._consumer = EventConsumer(PROJECTION_TOPICS, group_id=f"api-projection-{uuid4()}")
        self._thread: Thread | None = None

    def start(self) -> None:
        self._thread = Thread(target=self._consumer.run, args=(self.projection.apply,), daemon=True)
        self._thread.start()
        logger.info("projection stream started")

    def stop(self) -> None:
        self._consumer.stop()
        if self._thread:
            self._thread.join(timeout=5)
