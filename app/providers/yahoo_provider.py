from __future__ import annotations

from app.models import PriceQuote
from app.providers.base import PriceProvider


class YahooFinanceProvider(PriceProvider):
    source = "yahoo"

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        raise NotImplementedError("Yahoo Finance provider 预留在此，MVP 阶段暂未接入。")

