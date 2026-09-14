import logging

from ..domain.enums import OrderStatus
from ..events.envelope import Event
from ..events.payloads import order_from_payload, order_to_payload, trade_to_payload
from ..events.topics import Topic
from ..events.types import EventType
from ..services.matching import MatchingEngine
from .base import Worker

logger = logging.getLogger(__name__)


class MatchingWorker(Worker):
    name = "matching-worker"
    topics = [Topic.ORDER_EVENTS, Topic.ORDER_COMMANDS]

    def __init__(self) -> None:
        self.engine = MatchingEngine()
        super().__init__()

    def register(self) -> None:
        self.router.on(EventType.ORDER_ACCEPTED)(self.match_order)
        self.router.on(EventType.ORDER_CANCEL_REQUESTED)(self.cancel_order)

    def match_order(self, event: Event) -> None:
        order = order_from_payload(event.payload)
        currency = event.payload.get("currency", "USD")
        for trade in self.engine.submit(order):
            self.emit(Topic.TRADE_EVENTS, EventType.TRADE_EXECUTED, trade.symbol, trade_to_payload(trade, currency), event)
        self._emit_fill_state(order, currency, event)

    def cancel_order(self, event: Event) -> None:
        payload = event.payload
        if not self.engine.cancel(payload["symbol"], payload["order_id"]):
            return
        self.emit(Topic.ORDER_EVENTS, EventType.ORDER_CANCELLED, payload["symbol"], payload, event)

    def _emit_fill_state(self, order, currency: str, source: Event) -> None:
        if order.filled_quantity <= 0:
            return
        filled = order.remaining <= 0
        order.status = OrderStatus.FILLED if filled else OrderStatus.PARTIALLY_FILLED
        event_type = EventType.ORDER_FILLED if filled else EventType.ORDER_PARTIALLY_FILLED
        self.emit(Topic.ORDER_EVENTS, event_type, order.symbol, order_to_payload(order, currency), source)
