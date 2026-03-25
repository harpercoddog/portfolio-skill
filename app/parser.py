from __future__ import annotations

import re
from datetime import date

from app.models import ParsedTrade, TransactionType
from app.utils.money import quant_money, quant_qty, to_decimal

NUMBER_RE = r"([0-9]+(?:\.[0-9]+)?)"
ACCOUNT_PATTERNS = (
    re.compile(r"账户(?:是|为|=)?\s*([A-Za-z0-9_\-\u4e00-\u9fa5]+账户?)"),
    re.compile(r"([A-Za-z0-9_\-\u4e00-\u9fa5]+账户)"),
)
PRICE_PATTERNS = (
    re.compile(r"(?:价格|价(?:格)?|price|单价|成本|cost)\s*(?:是|为|=)?\s*" + NUMBER_RE, re.IGNORECASE),
)
FEE_PATTERNS = (
    re.compile(r"(?:手续费|fee)\s*(?:是|为|=)?\s*" + NUMBER_RE, re.IGNORECASE),
)

ACTION_PATTERNS: dict[TransactionType, re.Pattern[str]] = {
    TransactionType.BUY: re.compile(
        r"(?:买入|buy)\s+([A-Za-z0-9._-]+)\s+" + NUMBER_RE + r"\s*(?:股|份|shares?|units?)?",
        re.IGNORECASE,
    ),
    TransactionType.SELL: re.compile(
        r"(?:卖出|sell)\s+([A-Za-z0-9._-]+)\s+" + NUMBER_RE + r"\s*(?:股|份|shares?|units?)?",
        re.IGNORECASE,
    ),
    TransactionType.TRANSFER_IN: re.compile(
        r"(?:转入|transfer\s+in)\s+([A-Za-z0-9._-]+)\s+" + NUMBER_RE + r"\s*(?:股|份|shares?|units?)?",
        re.IGNORECASE,
    ),
    TransactionType.TRANSFER_OUT: re.compile(
        r"(?:转出|transfer\s+out)\s+([A-Za-z0-9._-]+)\s+" + NUMBER_RE + r"\s*(?:股|份|shares?|units?)?",
        re.IGNORECASE,
    ),
    TransactionType.DIVIDEND: re.compile(
        r"(?:分红|股息|dividend)\s+([A-Za-z0-9._-]+)\s+" + NUMBER_RE,
        re.IGNORECASE,
    ),
}


def normalize_text(text: str) -> str:
    return (
        text.replace("，", " ")
        .replace("。", " ")
        .replace(",", " ")
        .replace("：", " ")
        .replace(":", " ")
        .replace("（", " ")
        .replace("）", " ")
        .replace("(", " ")
        .replace(")", " ")
        .strip()
    )


def detect_transaction_type(text: str) -> TransactionType:
    lowered = text.lower()
    if "买入" in text or "buy" in lowered:
        return TransactionType.BUY
    if "卖出" in text or "sell" in lowered:
        return TransactionType.SELL
    if "分红" in text or "股息" in text or "dividend" in lowered:
        return TransactionType.DIVIDEND
    if "转入" in text or "transfer in" in lowered:
        return TransactionType.TRANSFER_IN
    if "转出" in text or "transfer out" in lowered:
        return TransactionType.TRANSFER_OUT
    raise ValueError("无法识别交易类型，请使用买入、卖出、分红、转入或转出。")


def extract_account_name(text: str) -> str:
    for pattern in ACCOUNT_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return "默认账户"


def extract_price(text: str) -> str | None:
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def extract_fee(text: str) -> str:
    for pattern in FEE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return "0"


def infer_market(symbol: str, account_name: str, raw_text: str) -> str:
    text = f"{raw_text} {account_name}"
    if "美股" in text or symbol.isalpha():
        return "US"
    if "港股" in text:
        return "HK"
    if "A股" in text or "沪深" in text or symbol.isdigit():
        return "CN"
    return "US"


def infer_currency(market: str) -> str:
    return {
        "US": "USD",
        "CN": "CNY",
        "HK": "HKD",
    }.get(market, "USD")


def infer_asset_type(symbol: str, market: str) -> str:
    if market == "CN" and symbol.isdigit() and symbol.startswith(("1", "5")):
        return "ETF"
    return "STOCK"


def parse_trade_text(text: str, trade_date: date | None = None) -> ParsedTrade:
    cleaned = normalize_text(text)
    transaction_type = detect_transaction_type(cleaned)
    match = ACTION_PATTERNS[transaction_type].search(cleaned)
    if not match:
        raise ValueError("无法解析标的和数量，请参考示例：买入 AAPL 10 股，价格 210，账户是美股账户")

    symbol = match.group(1).upper()
    amount_text = match.group(2)
    account_name = extract_account_name(cleaned)
    market = infer_market(symbol=symbol, account_name=account_name, raw_text=cleaned)
    currency = infer_currency(market)
    asset_type = infer_asset_type(symbol=symbol, market=market)
    fee = quant_money(to_decimal(extract_fee(cleaned)))

    quantity = quant_qty(to_decimal("0" if transaction_type == TransactionType.DIVIDEND else amount_text))
    unit_price = quant_money(to_decimal("0"))
    gross_amount = quant_money(to_decimal("0"))

    if transaction_type == TransactionType.DIVIDEND:
        gross_amount = quant_money(to_decimal(amount_text))
    else:
        price_text = extract_price(cleaned)
        if transaction_type in {TransactionType.BUY, TransactionType.SELL, TransactionType.TRANSFER_IN} and not price_text:
            raise ValueError("当前交易需要价格或成本信息，请补充“价格 123.45”或“成本 123.45”。")
        if price_text:
            unit_price = quant_money(to_decimal(price_text))
            gross_amount = quant_money(quantity * unit_price)

    return ParsedTrade(
        transaction_type=transaction_type,
        symbol=symbol,
        quantity=quantity,
        unit_price=unit_price,
        gross_amount=gross_amount,
        fee=fee,
        account_name=account_name,
        market=market,
        currency=currency,
        asset_type=asset_type,
        trade_date=trade_date or date.today(),
        raw_text=text.strip(),
    )

