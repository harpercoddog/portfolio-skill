from __future__ import annotations

from decimal import Decimal

from app.config import BASE_CURRENCY
from app.utils.money import quant_money


class FxService:
    # MVP static FX table for reporting aggregation.
    RATES_TO_CNY: dict[str, Decimal] = {
        "CNY": Decimal("1"),
        "USD": Decimal("7.20"),
        "HKD": Decimal("0.92"),
    }

    @classmethod
    def rate_to_cny(cls, currency: str | None) -> Decimal:
        if not currency:
            return Decimal("1")
        return cls.RATES_TO_CNY.get(currency.upper(), Decimal("1"))

    @classmethod
    def convert(cls, amount: Decimal | None, currency: str | None, target_currency: str = BASE_CURRENCY) -> Decimal | None:
        if amount is None:
            return None
        source_currency = (currency or target_currency).upper()
        target = target_currency.upper()
        if source_currency == target:
            return quant_money(amount)
        if target != "CNY":
            raise ValueError(f"MVP 仅支持换算到 CNY，当前请求目标币种为 {target_currency}")
        return quant_money(amount * cls.rate_to_cny(source_currency))
