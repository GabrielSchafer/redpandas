from trading.events.envelope import Event
from trading.events.types import EventType
from trading.store.projections import Projection


def test_projection_tracks_account_and_trades():
    projection = Projection()
    projection.apply(Event(EventType.ACCOUNT_OPENED, "acc", {"account_id": "acc", "owner": "Alice", "base_currency": "USD"}))
    projection.apply(
        Event(
            EventType.FUNDS_DEPOSITED,
            "acc",
            {"account_id": "acc", "currency": "USD", "amount": "100", "available": "100.00", "reserved": "0.00"},
        )
    )
    projection.apply(
        Event(
            EventType.TRADE_EXECUTED,
            "AAPL",
            {
                "trade_id": "t1",
                "symbol": "AAPL",
                "price": "190.00",
                "quantity": "1",
                "buy_order_id": "b1",
                "sell_order_id": "s1",
                "buyer_account_id": "acc",
                "seller_account_id": "other",
                "taker_side": "buy",
            },
        )
    )

    assert projection.accounts["acc"]["balances"]["USD"]["available"] == "100.00"
    assert projection.last_price["AAPL"] == "190.00"
    assert projection.orders["b1"]["last_trade_price"] == "190.00"
