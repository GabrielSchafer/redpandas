from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Trade:
    trade_id: str
    symbol: str
    price: Decimal
    quantity: Decimal
    buy_order_id: str
    sell_order_id: str
    buyer_account_id: str
    seller_account_id: str
    taker_side: str
