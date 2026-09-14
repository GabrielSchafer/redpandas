from dataclasses import dataclass, field
from decimal import Decimal

from .money import money, quantity


@dataclass
class Balance:
    currency: str
    available: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return money(self.available + self.reserved)


@dataclass
class Position:
    symbol: str
    quantity: Decimal = Decimal("0")
    reserved: Decimal = Decimal("0")
    average_price: Decimal = Decimal("0")

    @property
    def free(self) -> Decimal:
        return quantity(self.quantity - self.reserved)


@dataclass
class Account:
    account_id: str
    owner: str
    base_currency: str = "USD"
    balances: dict[str, Balance] = field(default_factory=dict)
    positions: dict[str, Position] = field(default_factory=dict)

    def balance(self, currency: str) -> Balance:
        return self.balances.setdefault(currency, Balance(currency=currency))

    def position(self, symbol: str) -> Position:
        return self.positions.setdefault(symbol, Position(symbol=symbol))
