from app.providers.auto_provider import AutoPriceProvider
from app.providers.akshare_provider import AkShareProvider
from app.providers.mock_provider import MockPriceProvider
from app.providers.yahoo_provider import YahooFinanceProvider


def build_provider(name: str):
    normalized = name.lower().strip()
    if normalized == "auto":
        return AutoPriceProvider()
    if normalized == "mock":
        return MockPriceProvider()
    if normalized == "yahoo":
        return YahooFinanceProvider()
    if normalized == "akshare":
        return AkShareProvider()
    raise ValueError(f"未知价格源: {name}")
