from decimal import Decimal, ROUND_HALF_EVEN

CASH_EXP = Decimal("0.01")
QTY_EXP = Decimal("0.00000001")


def to_decimal(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def money(value) -> Decimal:
    return to_decimal(value).quantize(CASH_EXP, rounding=ROUND_HALF_EVEN)


def quantity(value) -> Decimal:
    return to_decimal(value).quantize(QTY_EXP, rounding=ROUND_HALF_EVEN)


def notional(price, qty) -> Decimal:
    return money(to_decimal(price) * to_decimal(qty))
