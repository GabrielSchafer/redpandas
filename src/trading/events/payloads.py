from decimal import Decimal

from ..domain.enums import OrderType, Side
from ..domain.order import Order
from ..domain.trade import Trade


def order_to_payload(order: Order, currency: str) -> dict:
    return {
        "order_id": order.order_id,
        "account_id": order.account_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "order_type": order.order_type.value,
        "quantity": str(order.quantity),
        "price": str(order.price) if order.price is not None else None,
        "filled_quantity": str(order.filled_quantity),
        "status": order.status.value,
        "currency": currency,
    }


def order_from_payload(payload: dict) -> Order:
    price = payload.get("price")
    return Order(
        order_id=payload["order_id"],
        account_id=payload["account_id"],
        symbol=payload["symbol"],
        side=Side(payload["side"]),
        order_type=OrderType(payload["order_type"]),
        quantity=Decimal(payload["quantity"]),
        price=Decimal(price) if price else None,
        filled_quantity=Decimal(payload.get("filled_quantity", "0")),
    )


def trade_to_payload(trade: Trade, currency: str) -> dict:
    return {
        "trade_id": trade.trade_id,
        "symbol": trade.symbol,
        "price": str(trade.price),
        "quantity": str(trade.quantity),
        "buy_order_id": trade.buy_order_id,
        "sell_order_id": trade.sell_order_id,
        "buyer_account_id": trade.buyer_account_id,
        "seller_account_id": trade.seller_account_id,
        "taker_side": trade.taker_side,
        "currency": currency,
    }


def trade_from_payload(payload: dict) -> Trade:
    return Trade(
        trade_id=payload["trade_id"],
        symbol=payload["symbol"],
        price=Decimal(payload["price"]),
        quantity=Decimal(payload["quantity"]),
        buy_order_id=payload["buy_order_id"],
        sell_order_id=payload["sell_order_id"],
        buyer_account_id=payload["buyer_account_id"],
        seller_account_id=payload["seller_account_id"],
        taker_side=payload["taker_side"],
    )
