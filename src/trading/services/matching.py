from decimal import Decimal
from uuid import uuid4

from ..domain.enums import OrderType, Side
from ..domain.money import quantity
from ..domain.order import Order
from ..domain.trade import Trade
from .order_book import BookEntry, OrderBook


class MatchingEngine:
    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}

    def book(self, symbol: str) -> OrderBook:
        return self._books.setdefault(symbol, OrderBook(symbol))

    def cancel(self, symbol: str, order_id: str) -> bool:
        return self.book(symbol).remove(order_id) is not None

    def submit(self, order: Order) -> list[Trade]:
        book = self.book(order.symbol)
        trades = [trade for trade in self._match(order, book)]
        book.prune()
        if order.remaining > 0 and order.order_type is OrderType.LIMIT:
            book.add(BookEntry(order.order_id, order.account_id, order.side, order.price, order.remaining))
        return trades

    def _match(self, order: Order, book: OrderBook):
        for maker in list(book.opposite_book(order.side)):
            if order.remaining <= 0 or not self._crosses(order, maker.price):
                break
            traded = quantity(min(order.remaining, maker.remaining))
            maker.remaining = quantity(maker.remaining - traded)
            order.filled_quantity = quantity(order.filled_quantity + traded)
            yield self._build_trade(order, maker, traded)

    @staticmethod
    def _crosses(order: Order, maker_price: Decimal) -> bool:
        if order.order_type is OrderType.MARKET:
            return True
        return order.price >= maker_price if order.side is Side.BUY else order.price <= maker_price

    @staticmethod
    def _build_trade(order: Order, maker: BookEntry, traded: Decimal) -> Trade:
        buy_is_taker = order.side is Side.BUY
        return Trade(
            trade_id=str(uuid4()),
            symbol=order.symbol,
            price=maker.price,
            quantity=traded,
            buy_order_id=order.order_id if buy_is_taker else maker.order_id,
            sell_order_id=maker.order_id if buy_is_taker else order.order_id,
            buyer_account_id=order.account_id if buy_is_taker else maker.account_id,
            seller_account_id=maker.account_id if buy_is_taker else order.account_id,
            taker_side=order.side.value,
        )
