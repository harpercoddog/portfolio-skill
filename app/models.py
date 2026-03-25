from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    DIVIDEND = "DIVIDEND"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    MANUAL_OPENING_POSITION = "MANUAL_OPENING_POSITION"


@dataclass(frozen=True)
class ParsedTrade:
    transaction_type: TransactionType
    symbol: str
    quantity: Decimal
    unit_price: Decimal
    gross_amount: Decimal
    fee: Decimal
    account_name: str
    market: str
    currency: str
    asset_type: str
    trade_date: date
    raw_text: str


@dataclass(frozen=True)
class AssetRef:
    symbol: str
    market: str
    currency: str


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    market: str
    currency: str
    price_date: date
    close_price: Decimal
    prev_close_price: Decimal | None
    source: str


@dataclass
class PositionState:
    quantity: Decimal = Decimal("0")
    average_cost: Decimal = Decimal("0")
    total_cost_basis: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
