from __future__ import annotations

import sqlite3

from app.models import AssetRef
from app.providers import build_provider


def load_active_assets(conn: sqlite3.Connection) -> list[AssetRef]:
    rows = conn.execute(
        """
        SELECT DISTINCT ast.symbol, ast.market, ast.currency
        FROM assets ast
        JOIN transactions tx ON tx.asset_id = ast.id
        WHERE ast.is_active = 1
        ORDER BY ast.market ASC, ast.symbol ASC
        """
    ).fetchall()
    return [AssetRef(symbol=row["symbol"], market=row["market"], currency=row["currency"]) for row in rows]


def sync_prices(conn: sqlite3.Connection, provider_name: str = "mock") -> list[dict]:
    provider = build_provider(provider_name)
    assets = load_active_assets(conn)
    if not assets:
        return []

    results: list[dict] = []
    for asset in assets:
        try:
            quote = provider.get_latest_price(symbol=asset.symbol, market=asset.market, currency=asset.currency)
            asset_row = conn.execute(
                "SELECT id FROM assets WHERE symbol = ? AND market = ?",
                (quote.symbol, quote.market),
            ).fetchone()
            if not asset_row:
                continue

            conn.execute(
                """
                INSERT INTO price_history (
                    asset_id,
                    price_date,
                    close_price,
                    prev_close_price,
                    currency,
                    source
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id, price_date, source) DO UPDATE SET
                    close_price = excluded.close_price,
                    prev_close_price = excluded.prev_close_price,
                    currency = excluded.currency
                """,
                (
                    asset_row["id"],
                    quote.price_date.isoformat(),
                    str(quote.close_price),
                    str(quote.prev_close_price) if quote.prev_close_price is not None else None,
                    quote.currency,
                    quote.source,
                ),
            )
            conn.execute(
                """
                UPDATE assets
                SET
                    last_price = ?,
                    last_price_date = ?,
                    last_price_source = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    str(quote.close_price),
                    quote.price_date.isoformat(),
                    quote.source,
                    asset_row["id"],
                ),
            )
            results.append(
                {
                    "symbol": quote.symbol,
                    "market": quote.market,
                    "price_date": quote.price_date.isoformat(),
                    "close_price": str(quote.close_price),
                    "prev_close_price": str(quote.prev_close_price) if quote.prev_close_price is not None else None,
                    "source": quote.source,
                    "status": "ok",
                }
            )
        except Exception as exc:  # noqa: PERF203
            results.append(
                {
                    "symbol": asset.symbol,
                    "market": asset.market,
                    "price_date": None,
                    "close_price": None,
                    "prev_close_price": None,
                    "source": provider_name,
                    "status": "error",
                    "error": str(exc),
                }
            )

    conn.commit()
    return results
