from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import akshare as ak

from app.models import PriceQuote
from app.providers.base import PriceProvider
from app.utils.money import quant_money


class AkShareProvider(PriceProvider):
    source = "akshare"

    @staticmethod
    def _to_date(value) -> datetime.date:
        text = str(value).strip()
        if "-" in text:
            return datetime.strptime(text, "%Y-%m-%d").date()
        return datetime.strptime(text, "%Y%m%d").date()

    @staticmethod
    def _to_decimal(value) -> Decimal:
        return Decimal(str(value))

    @staticmethod
    def _recent_date_window() -> tuple[str, str]:
        today = datetime.today().date()
        start = today.fromordinal(today.toordinal() - 45)
        return start.strftime("%Y%m%d"), today.strftime("%Y%m%d")

    def _latest_cn_stock_or_etf(self, symbol: str) -> PriceQuote:
        start_date, end_date = self._recent_date_window()
        loader = ak.fund_etf_hist_em if symbol.startswith(("1", "5")) else ak.stock_zh_a_hist
        data_frame = loader(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="",
        )
        if data_frame.empty:
            raise ValueError(f"AkShare 未返回 A 股/ETF 价格: {symbol}")

        latest_row = data_frame.iloc[-1]
        prev_close = None
        if len(data_frame.index) >= 2:
            prev_close = quant_money(self._to_decimal(data_frame.iloc[-2]["收盘"]))

        return PriceQuote(
            symbol=symbol,
            market="CN",
            currency="CNY",
            price_date=self._to_date(latest_row["日期"]),
            close_price=quant_money(self._to_decimal(latest_row["收盘"])),
            prev_close_price=prev_close,
            source=self.source,
        )

    def get_latest_price(self, symbol: str, market: str, currency: str) -> PriceQuote:
        market_normalized = market.upper().strip()
        if market_normalized in {"CN", "A", "ASHARE"}:
            return self._latest_cn_stock_or_etf(symbol=symbol)
        raise ValueError(f"AkShareProvider 当前只处理中国市场标的: {symbol} ({market})")
