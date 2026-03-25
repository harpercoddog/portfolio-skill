from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

QTY_PRECISION = Decimal("0.000001")
MONEY_PRECISION = Decimal("0.0001")


def to_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def quant_money(value: object) -> Decimal:
    return to_decimal(value).quantize(MONEY_PRECISION, rounding=ROUND_HALF_UP)


def quant_qty(value: object) -> Decimal:
    return to_decimal(value).quantize(QTY_PRECISION, rounding=ROUND_HALF_UP)


def safe_divide(numerator: object | None, denominator: object | None) -> Decimal | None:
    if numerator is None or denominator is None:
        return None
    denominator_decimal = to_decimal(denominator)
    if denominator_decimal == 0:
        return None
    return to_decimal(numerator) / denominator_decimal


def format_decimal(value: object | None) -> str:
    if value is None:
        return "N/A"
    return f"{to_decimal(value):,.4f}"


def format_percent(value: object | None) -> str:
    if value is None:
        return "N/A"
    return f"{to_decimal(value):.2%}"

