from __future__ import annotations

from app.models import PriceQuote
from app.providers.akshare_provider import AkShareProvider
from app.providers.base import PriceProvider
from app.providers.yahoo_provider import YahooFinanceProvider


class AutoPriceProvider(PriceProvider):
    source = "auto"

    def __init__(self) -> None:
        self.yahoo_provider = YahooFinanceProvider()
        self.akshare_provider = AkShareProvider()

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        market_normalized = market.upper().strip()
        if market_normalized in {"CN", "A", "ASHARE"}:
            errors: list[str] = []
            for provider in (self.akshare_provider, self.yahoo_provider):
                try:
                    return provider.get_latest_price(symbol=symbol, market=market, currency=currency)
                except Exception as exc:  # noqa: PERF203
                    errors.append(f"{provider.source}: {exc}")
            raise ValueError(f"无法获取 {symbol} ({market}) 的价格，尝试结果: {'; '.join(errors)}")
        if market_normalized in {"US", "HK"}:
            errors = []
            for provider in (self.yahoo_provider, self.akshare_provider):
                try:
                    return provider.get_latest_price(symbol=symbol, market=market, currency=currency)
                except Exception as exc:  # noqa: PERF203
                    errors.append(f"{provider.source}: {exc}")
            raise ValueError(f"无法获取 {symbol} ({market}) 的价格，尝试结果: {'; '.join(errors)}")
        return self.yahoo_provider.get_latest_price(symbol=symbol, market=market, currency=currency)
