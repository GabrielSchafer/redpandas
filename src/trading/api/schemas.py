from decimal import Decimal

from pydantic import BaseModel, Field

from ..domain.enums import OrderType, Side


class AccountRequest(BaseModel):
    account_id: str
    owner: str
    base_currency: str = "USD"


class FundsRequest(BaseModel):
    currency: str = "USD"
    amount: Decimal = Field(gt=0)


class AssetRequest(BaseModel):
    symbol: str
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)


class OrderRequest(BaseModel):
    account_id: str
    symbol: str
    side: Side
    order_type: OrderType = OrderType.LIMIT
    quantity: Decimal = Field(gt=0)
    price: Decimal | None = Field(default=None, gt=0)
    currency: str = "USD"


class CommandAccepted(BaseModel):
    status: str = "accepted"
    event_type: str
    reference: str
