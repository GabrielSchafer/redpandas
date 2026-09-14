from decimal import Decimal

from ..domain.enums import EntryType
from ..domain.money import money, notional, quantity
from ..domain.trade import Trade
from .ledger import Ledger


def settle(ledger: Ledger, trade: Trade, currency: str) -> list[dict]:
    value = notional(trade.price, trade.quantity)
    _settle_buyer(ledger, trade, currency, value)
    _settle_seller(ledger, trade, currency, value)
    return _entries(trade, currency, value)


def _settle_buyer(ledger: Ledger, trade: Trade, currency: str, value: Decimal) -> None:
    balance = ledger.get(trade.buyer_account_id).balance(currency)
    balance.reserved = money(balance.reserved - min(balance.reserved, value))
    ledger.credit_asset(trade.buyer_account_id, trade.symbol, trade.quantity, trade.price)


def _settle_seller(ledger: Ledger, trade: Trade, currency: str, value: Decimal) -> None:
    position = ledger.get(trade.seller_account_id).position(trade.symbol)
    position.reserved = quantity(position.reserved - min(position.reserved, trade.quantity))
    position.quantity = quantity(position.quantity - trade.quantity)
    balance = ledger.get(trade.seller_account_id).balance(currency)
    balance.available = money(balance.available + value)


def _entries(trade: Trade, currency: str, value: Decimal) -> list[dict]:
    common = {"trade_id": trade.trade_id, "symbol": trade.symbol, "currency": currency, "amount": value}
    return [
        {**common, "account_id": trade.buyer_account_id, "type": EntryType.TRADE_DEBIT.value},
        {**common, "account_id": trade.seller_account_id, "type": EntryType.TRADE_CREDIT.value},
    ]
