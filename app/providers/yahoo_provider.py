from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import yfinance as yf

from app.models import PriceQuote
from app.providers.base import PriceProvider
from app.utils.money import quant_money


class YahooFinanceProvider(PriceProvider):
    source = "yahoo"

    @staticmethod
    def _normalize_symbol(symbol: str, market: str) -> str:
        raw = symbol.strip().upper()
        market_normalized = market.upper().strip()
        if market_normalized == "HK":
            if raw.endswith(".HK"):
                return raw
            digits = raw.split(".")[0]
            if digits.isdigit():
                return f"{digits.zfill(4)}.HK"
        if market_normalized in {"CN", "A", "ASHARE"}:
            if raw.endswith((".SS", ".SZ")):
                return raw
            digits = raw.split(".")[0]
            if digits.isdigit():
                suffix = ".SS" if digits.startswith(("5", "6", "9")) else ".SZ"
                return f"{digits}{suffix}"
        return raw

    @staticmethod
    def _to_date(index_value) -> datetime.date:
        if hasattr(index_value, "to_pydatetime"):
            return index_value.to_pydatetime().date()
        if hasattr(index_value, "date"):
            return index_value.date()
        return datetime.fromisoformat(str(index_value)).date()

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        yahoo_symbol = self._normalize_symbol(symbol=symbol, market=market)
        ticker = yf.Ticker(yahoo_symbol)
        history = ticker.history(period="5d", interval="1d", auto_adjust=False)
        if history.empty:
            raise ValueError(f"Yahoo Finance 未返回价格: {symbol} ({market})")

        latest_row = history.iloc[-1]
        latest_idx = history.index[-1]
        prev_close = None
        if len(history.index) >= 2:
            prev_close = quant_money(Decimal(str(history.iloc[-2]["Close"])))

        return PriceQuote(
            symbol=symbol,
            market=market,
            currency=currency,
            price_date=self._to_date(latest_idx),
            close_price=quant_money(Decimal(str(latest_row["Close"]))),
            prev_close_price=prev_close,
            source=self.source,
        )
