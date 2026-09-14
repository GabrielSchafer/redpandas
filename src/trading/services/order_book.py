from dataclasses import dataclass, field
from decimal import Decimal
from itertools import count

from ..domain.enums import Side


@dataclass
class BookEntry:
    order_id: str
    account_id: str
    side: Side
    price: Decimal
    remaining: Decimal
    sequence: int = field(default_factory=count().__next__)


class OrderBook:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self._bids: list[BookEntry] = []
        self._asks: list[BookEntry] = []

    def side_book(self, side: Side) -> list[BookEntry]:
        return self._bids if side is Side.BUY else self._asks

    def opposite_book(self, side: Side) -> list[BookEntry]:
        return self._asks if side is Side.BUY else self._bids

    def add(self, entry: BookEntry) -> None:
        book = self.side_book(entry.side)
        book.append(entry)
        reverse = entry.side is Side.BUY
        book.sort(key=lambda item: (-item.price if reverse else item.price, item.sequence))

    def remove(self, order_id: str) -> BookEntry | None:
        for book in (self._bids, self._asks):
            for entry in book:
                if entry.order_id == order_id:
                    book.remove(entry)
                    return entry
        return None

    def prune(self) -> None:
        self._bids = [entry for entry in self._bids if entry.remaining > 0]
        self._asks = [entry for entry in self._asks if entry.remaining > 0]

    def depth(self, levels: int = 5) -> dict[str, list[dict]]:
        return {
            "bids": [self._level(entry) for entry in self._bids[:levels]],
            "asks": [self._level(entry) for entry in self._asks[:levels]],
        }

    @staticmethod
    def _level(entry: BookEntry) -> dict:
        return {"price": str(entry.price), "quantity": str(entry.remaining), "order_id": entry.order_id}
