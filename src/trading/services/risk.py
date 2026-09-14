from decimal import Decimal

from ..domain.enums import OrderType, Side
from ..domain.money import notional, to_decimal
from ..domain.order import Order
from .ledger import Ledger, LedgerError

MARKET_PRICE_BUFFER = Decimal("1.05")


class RiskEngine:
    def __init__(self, ledger: Ledger, max_order_notional: Decimal = Decimal("1000000")) -> None:
        self._ledger = ledger
        self._max_notional = max_order_notional
        self._last_price: dict[str, Decimal] = {}

    def track_price(self, symbol: str, price) -> None:
        self._last_price[symbol] = to_decimal(price)

    def evaluate(self, order: Order, currency: str) -> str | None:
        if order.quantity <= 0:
            return "quantity must be positive"
        price = self._reference_price(order)
        if price is None:
            return "no reference price for market order"
        if notional(price, order.quantity) > self._max_notional:
            return "order notional above risk limit"
        try:
            self._reserve(order, currency, price)
        except LedgerError as error:
            return str(error)
        return None

    def release(self, order: Order, currency: str) -> None:
        if order.side is Side.BUY:
            price = self._reference_price(order) or Decimal("0")
            self._ledger.release_cash(order.account_id, currency, notional(price, order.remaining))
        else:
            self._ledger.release_asset(order.account_id, order.symbol, order.remaining)

    def _reserve(self, order: Order, currency: str, price: Decimal) -> None:
        if order.side is Side.BUY:
            self._ledger.reserve_cash(order.account_id, currency, notional(price, order.quantity))
        else:
            self._ledger.reserve_asset(order.account_id, order.symbol, order.quantity)

    def _reference_price(self, order: Order) -> Decimal | None:
        if order.order_type is OrderType.LIMIT:
            return order.price
        last = self._last_price.get(order.symbol)
        return last * MARKET_PRICE_BUFFER if last else None
