from __future__ import annotations

import hashlib
from datetime import date, timedelta
from decimal import Decimal

from app.models import PriceQuote
from app.providers.base import PriceProvider
from app.utils.money import quant_money


class MockPriceProvider(PriceProvider):
    source = "mock"

    @staticmethod
    def _deterministic_price(symbol: str, market: str, on_date: date) -> Decimal:
        payload = f"{market}:{symbol}:{on_date.isoformat()}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        base_value = int(digest[:8], 16) % 8000
        anchor = Decimal("20") if market == "US" else Decimal("3")
        price = anchor + Decimal(base_value) / Decimal("100")
        return quant_money(price)

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        today = date.today()
        prev_day = today - timedelta(days=1)
        return PriceQuote(
            symbol=symbol,
            market=market,
            currency=currency,
            price_date=today,
            close_price=self._deterministic_price(symbol=symbol, market=market, on_date=today),
            prev_close_price=self._deterministic_price(symbol=symbol, market=market, on_date=prev_day),
            source=self.source,
        )

