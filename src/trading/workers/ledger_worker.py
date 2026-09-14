import logging

from ..events.envelope import Event
from ..events.payloads import trade_from_payload
from ..events.topics import Topic
from ..events.types import EventType
from ..services.ledger import Ledger, LedgerError
from ..services.settlement import settle
from .account_commands import AccountCommandsMixin
from .base import Worker

logger = logging.getLogger(__name__)


class LedgerWorker(AccountCommandsMixin, Worker):
    name = "ledger-worker"
    topics = [Topic.ACCOUNT_COMMANDS, Topic.TRADE_EVENTS]

    def __init__(self) -> None:
        self.ledger = Ledger()
        super().__init__()

    def register(self) -> None:
        self.router.on(EventType.ACCOUNT_OPEN_REQUESTED)(self.open_account)
        self.router.on(EventType.DEPOSIT_REQUESTED)(self.deposit)
        self.router.on(EventType.WITHDRAW_REQUESTED)(self.withdraw)
        self.router.on(EventType.CREDIT_ASSET_REQUESTED)(self.credit_assets)
        self.router.on(EventType.TRADE_EXECUTED)(self.settle_trade)

    def settle_trade(self, event: Event) -> None:
        trade = trade_from_payload(event.payload)
        currency = event.payload.get("currency", self.ledger.base_currency)
        try:
            entries = settle(self.ledger, trade, currency)
        except LedgerError as error:
            logger.error("settlement failed for trade %s: %s", trade.trade_id, error)
            return
        for entry in entries:
            self.emit(Topic.LEDGER_EVENTS, EventType.LEDGER_ENTRY_RECORDED, entry["account_id"], entry, event)
        for account_id in (trade.buyer_account_id, trade.seller_account_id):
            self._emit_position(account_id, trade.symbol, event)

    def _emit_position(self, account_id: str, symbol: str, source: Event) -> None:
        position = self.ledger.get(account_id).position(symbol)
        self.emit(
            Topic.LEDGER_EVENTS,
            EventType.POSITION_UPDATED,
            account_id,
            {
                "account_id": account_id,
                "symbol": symbol,
                "quantity": str(position.quantity),
                "reserved": str(position.reserved),
                "average_price": str(position.average_price),
            },
            source,
        )
