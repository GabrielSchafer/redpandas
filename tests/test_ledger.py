from decimal import Decimal

import pytest

from trading.domain.trade import Trade
from trading.services.ledger import Ledger, LedgerError
from trading.services.settlement import settle


@pytest.fixture
def ledger() -> Ledger:
    book = Ledger()
    book.open_account("buyer", "Alice")
    book.open_account("seller", "Bob")
    book.deposit("buyer", "USD", Decimal("2000"))
    book.credit_asset("seller", "AAPL", Decimal("10"), Decimal("180"))
    return book


def test_reserve_blocks_available_cash(ledger: Ledger):
    ledger.reserve_cash("buyer", "USD", Decimal("1900"))
    balance = ledger.get("buyer").balance("USD")
    assert balance.available == Decimal("100.00")
    assert balance.reserved == Decimal("1900.00")


def test_reserve_above_balance_fails(ledger: Ledger):
    with pytest.raises(LedgerError):
        ledger.reserve_cash("buyer", "USD", Decimal("5000"))


def test_settlement_moves_cash_and_position(ledger: Ledger):
    ledger.reserve_cash("buyer", "USD", Decimal("1900"))
    ledger.reserve_asset("seller", "AAPL", Decimal("10"))
    trade = Trade("t1", "AAPL", Decimal("190"), Decimal("10"), "b1", "s1", "buyer", "seller", "buy")

    entries = settle(ledger, trade, "USD")

    assert ledger.get("buyer").position("AAPL").quantity == Decimal("10")
    assert ledger.get("buyer").balance("USD").reserved == Decimal("0.00")
    assert ledger.get("seller").balance("USD").available == Decimal("1900.00")
    assert ledger.get("seller").position("AAPL").quantity == Decimal("0")
    assert len(entries) == 2
