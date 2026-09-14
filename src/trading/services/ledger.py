from decimal import Decimal

from ..domain.account import Account, Balance
from ..domain.money import money, quantity


class LedgerError(Exception):
    pass


class Ledger:
    def __init__(self, base_currency: str = "USD") -> None:
        self.base_currency = base_currency
        self._accounts: dict[str, Account] = {}

    def accounts(self) -> list[Account]:
        return list(self._accounts.values())

    def get(self, account_id: str) -> Account:
        account = self._accounts.get(account_id)
        if account is None:
            raise LedgerError(f"unknown account: {account_id}")
        return account

    def open_account(self, account_id: str, owner: str, base_currency: str | None = None) -> Account:
        if account_id in self._accounts:
            raise LedgerError(f"account already exists: {account_id}")
        account = Account(account_id=account_id, owner=owner, base_currency=base_currency or self.base_currency)
        self._accounts[account_id] = account
        return account

    def deposit(self, account_id: str, currency: str, amount: Decimal) -> Balance:
        amount = money(amount)
        if amount <= 0:
            raise LedgerError("deposit amount must be positive")
        balance = self.get(account_id).balance(currency)
        balance.available = money(balance.available + amount)
        return balance

    def withdraw(self, account_id: str, currency: str, amount: Decimal) -> Balance:
        amount = money(amount)
        balance = self.get(account_id).balance(currency)
        if amount <= 0 or balance.available < amount:
            raise LedgerError("insufficient available balance")
        balance.available = money(balance.available - amount)
        return balance

    def reserve_cash(self, account_id: str, currency: str, amount: Decimal) -> None:
        amount = money(amount)
        balance = self.get(account_id).balance(currency)
        if balance.available < amount:
            raise LedgerError("insufficient funds to reserve")
        balance.available = money(balance.available - amount)
        balance.reserved = money(balance.reserved + amount)

    def release_cash(self, account_id: str, currency: str, amount: Decimal) -> None:
        amount = money(amount)
        balance = self.get(account_id).balance(currency)
        released = min(balance.reserved, amount)
        balance.reserved = money(balance.reserved - released)
        balance.available = money(balance.available + released)

    def reserve_asset(self, account_id: str, symbol: str, qty: Decimal) -> None:
        qty = quantity(qty)
        position = self.get(account_id).position(symbol)
        if position.free < qty:
            raise LedgerError("insufficient position to reserve")
        position.reserved = quantity(position.reserved + qty)

    def release_asset(self, account_id: str, symbol: str, qty: Decimal) -> None:
        position = self.get(account_id).position(symbol)
        position.reserved = quantity(position.reserved - min(position.reserved, quantity(qty)))

    def credit_asset(self, account_id: str, symbol: str, qty: Decimal, price: Decimal) -> None:
        position = self.get(account_id).position(symbol)
        total_cost = position.average_price * position.quantity + price * quantity(qty)
        position.quantity = quantity(position.quantity + qty)
        position.average_price = money(total_cost / position.quantity) if position.quantity else Decimal("0")
