from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ...domain.enums import OrderType
from ...events.envelope import Event
from ...events.topics import Topic
from ...events.types import EventType
from ..deps import get_producer, get_projection
from ..schemas import CommandAccepted, OrderRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=CommandAccepted, status_code=202)
def place_order(body: OrderRequest, producer=Depends(get_producer)) -> CommandAccepted:
    if body.order_type is OrderType.LIMIT and body.price is None:
        raise HTTPException(status_code=422, detail="limit orders require a price")
    order_id = str(uuid4())
    payload = {
        "order_id": order_id,
        "account_id": body.account_id,
        "symbol": body.symbol,
        "side": body.side.value,
        "order_type": body.order_type.value,
        "quantity": str(body.quantity),
        "price": str(body.price) if body.price is not None else None,
        "currency": body.currency,
        "status": "pending",
    }
    producer.publish(
        Topic.ORDER_COMMANDS,
        Event(type=EventType.ORDER_REQUESTED, key=body.account_id, payload=payload),
    )
    return CommandAccepted(event_type=EventType.ORDER_REQUESTED, reference=order_id)


@router.delete("/{order_id}", response_model=CommandAccepted, status_code=202)
def cancel_order(order_id: str, symbol: str, producer=Depends(get_producer)) -> CommandAccepted:
    payload = {"order_id": order_id, "symbol": symbol}
    producer.publish(
        Topic.ORDER_COMMANDS,
        Event(type=EventType.ORDER_CANCEL_REQUESTED, key=symbol, payload=payload),
    )
    return CommandAccepted(event_type=EventType.ORDER_CANCEL_REQUESTED, reference=order_id)


@router.get("/{order_id}")
def read_order(order_id: str, projection=Depends(get_projection)) -> dict:
    order = projection.orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not projected yet")
    return order
