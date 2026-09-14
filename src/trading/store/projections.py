from collections import deque

from ..events.envelope import Event
from ..events.types import EventType

MAX_TRADES = 500


class Projection:
    def __init__(self) -> None:
        self.accounts: dict[str, dict] = {}
        self.orders: dict[str, dict] = {}
        self.trades: deque[dict] = deque(maxlen=MAX_TRADES)
        self.last_price: dict[str, str] = {}

    def apply(self, event: Event) -> None:
        handler = _HANDLERS.get(event.type)
        if handler:
            handler(self, event.payload)

    def account(self, account_id: str) -> dict:
        return self.accounts.setdefault(account_id, {"balances": {}, "positions": {}})

    def _account_opened(self, payload: dict) -> None:
        account = self.account(payload["account_id"])
        account.update({"owner": payload["owner"], "base_currency": payload["base_currency"]})

    def _balance_changed(self, payload: dict) -> None:
        balances = self.account(payload["account_id"])["balances"]
        balances[payload["currency"]] = {"available": payload["available"], "reserved": payload["reserved"]}

    def _position_updated(self, payload: dict) -> None:
        positions = self.account(payload["account_id"])["positions"]
        positions[payload["symbol"]] = {
            "quantity": payload["quantity"],
            "reserved": payload["reserved"],
            "average_price": payload["average_price"],
        }

    def _order_changed(self, payload: dict) -> None:
        order = self.orders.setdefault(payload["order_id"], {})
        order.update(payload)

    def _order_cancelled(self, payload: dict) -> None:
        order = self.orders.setdefault(payload["order_id"], {})
        order["status"] = "cancelled"

    def _trade_executed(self, payload: dict) -> None:
        self.trades.appendleft(payload)
        self.last_price[payload["symbol"]] = payload["price"]
        for order_id in (payload["buy_order_id"], payload["sell_order_id"]):
            self.orders.setdefault(order_id, {"order_id": order_id})["last_trade_price"] = payload["price"]


_HANDLERS = {
    EventType.ACCOUNT_OPENED: Projection._account_opened,
    EventType.FUNDS_DEPOSITED: Projection._balance_changed,
    EventType.FUNDS_WITHDRAWN: Projection._balance_changed,
    EventType.POSITION_UPDATED: Projection._position_updated,
    EventType.ASSETS_CREDITED: Projection._position_updated,
    EventType.ORDER_REQUESTED: Projection._order_changed,
    EventType.ORDER_ACCEPTED: Projection._order_changed,
    EventType.ORDER_REJECTED: Projection._order_changed,
    EventType.ORDER_PARTIALLY_FILLED: Projection._order_changed,
    EventType.ORDER_FILLED: Projection._order_changed,
    EventType.ORDER_CANCELLED: Projection._order_cancelled,
    EventType.TRADE_EXECUTED: Projection._trade_executed,
}
