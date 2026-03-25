from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import AssetRef, PriceQuote


class PriceProvider(ABC):
    source = "unknown"

    @abstractmethod
    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        raise NotImplementedError

    def get_latest_prices(self, assets: list[AssetRef]) -> list[PriceQuote]:
        return [
            self.get_latest_price(symbol=asset.symbol, market=asset.market, currency=asset.currency)
            for asset in assets
        ]

