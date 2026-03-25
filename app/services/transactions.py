from __future__ import annotations

import sqlite3
from datetime import date

from app.models import ParsedTrade
from app.parser import parse_trade_text


def get_or_create_account(conn: sqlite3.Connection, name: str, market: str, base_currency: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM accounts WHERE name = ?", (name,)).fetchone()
    if row:
        conn.execute(
            """
            UPDATE accounts
            SET market = ?, base_currency = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (market, base_currency, row["id"]),
        )
        conn.commit()
        return conn.execute("SELECT * FROM accounts WHERE id = ?", (row["id"],)).fetchone()

    cursor = conn.execute(
        """
        INSERT INTO accounts (name, market, base_currency)
        VALUES (?, ?, ?)
        """,
        (name, market, base_currency),
    )
    conn.commit()
    return conn.execute("SELECT * FROM accounts WHERE id = ?", (cursor.lastrowid,)).fetchone()


def get_or_create_asset(
    conn: sqlite3.Connection,
    symbol: str,
    market: str,
    currency: str,
    asset_type: str,
) -> sqlite3.Row:
    row = conn.execute(
        "SELECT * FROM assets WHERE symbol = ? AND market = ?",
        (symbol, market),
    ).fetchone()
    if row:
        conn.execute(
            """
            UPDATE assets
            SET currency = ?, asset_type = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (currency, asset_type, row["id"]),
        )
        conn.commit()
        return conn.execute("SELECT * FROM assets WHERE id = ?", (row["id"],)).fetchone()

    cursor = conn.execute(
        """
        INSERT INTO assets (symbol, market, name, asset_type, currency, is_active)
        VALUES (?, ?, ?, ?, ?, 1)
        """,
        (symbol, market, symbol, asset_type, currency),
    )
    conn.commit()
    return conn.execute("SELECT * FROM assets WHERE id = ?", (cursor.lastrowid,)).fetchone()


def record_trade(
    conn: sqlite3.Connection,
    text: str,
    trade_date: date | None = None,
) -> dict:
    parsed: ParsedTrade = parse_trade_text(text=text, trade_date=trade_date)
    account = get_or_create_account(
        conn=conn,
        name=parsed.account_name,
        market=parsed.market,
        base_currency=parsed.currency,
    )
    asset = get_or_create_asset(
        conn=conn,
        symbol=parsed.symbol,
        market=parsed.market,
        currency=parsed.currency,
        asset_type=parsed.asset_type,
    )

    cursor = conn.execute(
        """
        INSERT INTO transactions (
            trade_date,
            transaction_type,
            account_id,
            asset_id,
            quantity,
            unit_price,
            gross_amount,
            fee,
            currency,
            note,
            raw_text
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            parsed.trade_date.isoformat(),
            parsed.transaction_type.value,
            account["id"],
            asset["id"],
            str(parsed.quantity),
            str(parsed.unit_price),
            str(parsed.gross_amount),
            str(parsed.fee),
            parsed.currency,
            parsed.raw_text,
            parsed.raw_text,
        ),
    )
    conn.commit()

    return {
        "transaction_id": cursor.lastrowid,
        "trade_date": parsed.trade_date.isoformat(),
        "transaction_type": parsed.transaction_type.value,
        "account_name": account["name"],
        "symbol": asset["symbol"],
        "market": asset["market"],
        "quantity": str(parsed.quantity),
        "unit_price": str(parsed.unit_price),
        "gross_amount": str(parsed.gross_amount),
        "fee": str(parsed.fee),
        "currency": parsed.currency,
    }

