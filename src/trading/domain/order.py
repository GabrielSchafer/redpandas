from dataclasses import dataclass
from decimal import Decimal

from .enums import OrderStatus, OrderType, Side


@dataclass
class Order:
    order_id: str
    account_id: str
    symbol: str
    side: Side
    order_type: OrderType
    quantity: Decimal
    price: Decimal | None = None
    filled_quantity: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.PENDING
    reject_reason: str | None = None

    @property
    def remaining(self) -> Decimal:
        return self.quantity - self.filled_quantity

    @property
    def is_closed(self) -> bool:
        return self.status in (OrderStatus.FILLED, OrderStatus.REJECTED, OrderStatus.CANCELLED)
