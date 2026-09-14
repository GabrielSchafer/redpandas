import logging
from decimal import Decimal

from ..domain.enums import OrderStatus
from ..events.envelope import Event
from ..events.payloads import order_from_payload, order_to_payload, trade_from_payload
from ..events.topics import Topic
from ..events.types import EventType
from ..services.ledger import Ledger, LedgerError
from ..services.risk import RiskEngine
from ..services.settlement import settle
from .base import Worker

logger = logging.getLogger(__name__)


class RiskWorker(Worker):
    name = "risk-worker"
    topics = [Topic.ORDER_COMMANDS, Topic.ACCOUNT_EVENTS, Topic.TRADE_EVENTS, Topic.ORDER_EVENTS]

    def __init__(self) -> None:
        self.ledger = Ledger()
        self.engine = RiskEngine(self.ledger)
        self._open_orders: dict[str, tuple] = {}
        super().__init__()

    def register(self) -> None:
        self.router.on(EventType.ACCOUNT_OPENED)(self.sync_account)
        self.router.on(EventType.FUNDS_DEPOSITED)(self.sync_deposit)
        self.router.on(EventType.FUNDS_WITHDRAWN)(self.sync_withdrawal)
        self.router.on(EventType.ASSETS_CREDITED)(self.sync_assets)
        self.router.on(EventType.TRADE_EXECUTED)(self.sync_trade)
        self.router.on(EventType.ORDER_REQUESTED)(self.screen_order)
        self.router.on(EventType.ORDER_CANCELLED)(self.release_order)

    def sync_account(self, event: Event) -> None:
        payload = event.payload
        try:
            self.ledger.open_account(payload["account_id"], payload["owner"], payload.get("base_currency"))
        except LedgerError:
            logger.debug("account already replicated: %s", payload["account_id"])

    def sync_deposit(self, event: Event) -> None:
        self._apply(self.ledger.deposit, event)

    def sync_withdrawal(self, event: Event) -> None:
        self._apply(self.ledger.withdraw, event)

    def sync_assets(self, event: Event) -> None:
        payload = event.payload
        try:
            self.ledger.credit_asset(
                payload["account_id"], payload["symbol"], Decimal(payload["credited_quantity"]), Decimal(payload["price"])
            )
        except LedgerError as error:
            logger.error("replica asset credit failed: %s", error)

    def sync_trade(self, event: Event) -> None:
        trade = trade_from_payload(event.payload)
        self.engine.track_price(trade.symbol, trade.price)
        try:
            settle(self.ledger, trade, event.payload.get("currency", self.ledger.base_currency))
        except LedgerError as error:
            logger.error("replica settlement failed: %s", error)

    def screen_order(self, event: Event) -> None:
        order = order_from_payload(event.payload)
        currency = event.payload.get("currency", self.ledger.base_currency)
        reason = self.engine.evaluate(order, currency)
        if reason:
            order.status = OrderStatus.REJECTED
            order.reject_reason = reason
            payload = order_to_payload(order, currency) | {"reason": reason}
            self.emit(Topic.ORDER_EVENTS, EventType.ORDER_REJECTED, order.account_id, payload, event)
            return
        order.status = OrderStatus.ACCEPTED
        self._open_orders[order.order_id] = (order, currency)
        self.emit(
            Topic.ORDER_EVENTS,
            EventType.ORDER_ACCEPTED,
            order.symbol,
            order_to_payload(order, currency),
            event,
        )

    def release_order(self, event: Event) -> None:
        entry = self._open_orders.pop(event.payload["order_id"], None)
        if entry is None:
            return
        order, currency = entry
        order.filled_quantity = Decimal(event.payload.get("filled_quantity", str(order.filled_quantity)))
        self.engine.release(order, currency)

    def _apply(self, operation, event: Event) -> None:
        payload = event.payload
        try:
            operation(payload["account_id"], payload["currency"], Decimal(payload["amount"]))
        except LedgerError as error:
            logger.error("replica sync failed: %s", error)
