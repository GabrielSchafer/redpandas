from collections import Counter, deque

from ..events.envelope import Event
from ..events.payloads import order_from_payload
from ..events.types import EventType
from ..services.matching import MatchingEngine
from ..store.projections import Projection

TAPE_SIZE = 14
REJECT_SIZE = 4


class MonitorState:
    """Read model for the terminal dashboard, folded from every topic."""

    def __init__(self) -> None:
        self.projection = Projection()
        self.engine = MatchingEngine()
        self.counts: Counter = Counter()
        self.last_type: dict[str, str] = {}
        self.tape: deque = deque(maxlen=TAPE_SIZE)
        self.rejects: deque = deque(maxlen=REJECT_SIZE)
        self.symbols: list[str] = []
        self.total = 0

    def apply(self, topic: str, event: Event) -> None:
        self.projection.apply(event)
        self.counts[topic] += 1
        self.last_type[topic] = event.type
        self.total += 1
        self.tape.appendleft((event.occurred_at[11:19], topic, event.type, event.key))
        self._track_symbol(event)
        self._shadow_book(event)

    @property
    def symbol(self) -> str | None:
        return self.symbols[0] if self.symbols else None

    def book(self, symbol: str, levels: int = 5) -> dict:
        return self.engine.book(symbol).depth(levels)

    def trades(self, limit: int) -> list[dict]:
        return list(self.projection.trades)[:limit]

    def _track_symbol(self, event: Event) -> None:
        symbol = event.payload.get("symbol")
        if symbol and symbol not in self.symbols:
            self.symbols.append(symbol)

    def _shadow_book(self, event: Event) -> None:
        if event.type == EventType.ORDER_ACCEPTED:
            self.engine.submit(order_from_payload(event.payload))
        elif event.type == EventType.ORDER_CANCELLED:
            self.engine.cancel(event.payload["symbol"], event.payload["order_id"])
        elif event.type == EventType.ORDER_REJECTED:
            self.rejects.appendleft(
                (event.payload.get("account_id", "?"), event.payload.get("reason", "rejected"))
            )
