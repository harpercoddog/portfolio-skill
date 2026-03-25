from __future__ import annotations

from app.models import PriceQuote
from app.providers.base import PriceProvider


class AkShareProvider(PriceProvider):
    source = "akshare"

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        raise NotImplementedError("AkShare provider 预留在此，MVP 阶段暂未接入。")

