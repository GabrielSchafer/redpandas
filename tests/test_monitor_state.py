from trading.events.envelope import Event
from trading.events.topics import Topic
from trading.events.types import EventType
from trading.monitor.state import MonitorState


def _order(order_id: str, side: str, price: str, quantity: str) -> dict:
    return {
        "order_id": order_id,
        "account_id": "acc-alpha",
        "symbol": "AAPL",
        "side": side,
        "order_type": "limit",
        "quantity": quantity,
        "price": price,
        "currency": "USD",
        "status": "accepted",
    }


def test_state_counts_events_and_tracks_symbol():
    state = MonitorState()
    state.apply(Topic.ORDER_EVENTS, Event(EventType.ORDER_ACCEPTED, "AAPL", _order("1", "sell", "190.00", "10")))

    assert state.counts[Topic.ORDER_EVENTS] == 1
    assert state.last_type[Topic.ORDER_EVENTS] == EventType.ORDER_ACCEPTED
    assert state.symbol == "AAPL"
    assert state.total == 1


def test_shadow_book_follows_accepted_and_cancelled_orders():
    state = MonitorState()
    state.apply(Topic.ORDER_EVENTS, Event(EventType.ORDER_ACCEPTED, "AAPL", _order("1", "sell", "190.00", "10")))
    assert state.book("AAPL")["asks"][0]["order_id"] == "1"

    state.apply(Topic.ORDER_EVENTS, Event(EventType.ORDER_CANCELLED, "AAPL", {"order_id": "1", "symbol": "AAPL"}))
    assert state.book("AAPL")["asks"] == []


def test_rejections_are_kept_for_display():
    state = MonitorState()
    payload = {"order_id": "9", "account_id": "acc-beta", "symbol": "AAPL", "reason": "insufficient funds to reserve"}
    state.apply(Topic.ORDER_EVENTS, Event(EventType.ORDER_REJECTED, "acc-beta", payload))

    assert state.rejects[0] == ("acc-beta", "insufficient funds to reserve")
