from decimal import Decimal

from trading.domain.enums import OrderType, Side
from trading.domain.order import Order
from trading.services.matching import MatchingEngine


def _order(order_id: str, account: str, side: Side, qty: str, price: str | None = None) -> Order:
    return Order(
        order_id=order_id,
        account_id=account,
        symbol="AAPL",
        side=side,
        order_type=OrderType.LIMIT if price else OrderType.MARKET,
        quantity=Decimal(qty),
        price=Decimal(price) if price else None,
    )


def test_resting_order_does_not_trade():
    engine = MatchingEngine()
    trades = engine.submit(_order("1", "seller", Side.SELL, "10", "190"))
    assert trades == []
    assert engine.book("AAPL").depth()["asks"][0]["price"] == "190"


def test_full_cross_generates_trade():
    engine = MatchingEngine()
    engine.submit(_order("1", "seller", Side.SELL, "10", "190"))
    trades = engine.submit(_order("2", "buyer", Side.BUY, "10", "191"))
    assert len(trades) == 1
    assert trades[0].price == Decimal("190")
    assert trades[0].buyer_account_id == "buyer"
    assert engine.book("AAPL").depth()["asks"] == []


def test_partial_fill_keeps_remainder():
    engine = MatchingEngine()
    engine.submit(_order("1", "seller", Side.SELL, "4", "190"))
    taker = _order("2", "buyer", Side.BUY, "10", "190")
    trades = engine.submit(taker)
    assert trades[0].quantity == Decimal("4")
    assert taker.remaining == Decimal("6")
    assert Decimal(engine.book("AAPL").depth()["bids"][0]["quantity"]) == Decimal("6")


def test_market_order_sweeps_price_levels():
    engine = MatchingEngine()
    engine.submit(_order("1", "seller", Side.SELL, "5", "190"))
    engine.submit(_order("2", "seller", Side.SELL, "5", "192"))
    trades = engine.submit(_order("3", "buyer", Side.BUY, "8"))
    assert [trade.price for trade in trades] == [Decimal("190"), Decimal("192")]
