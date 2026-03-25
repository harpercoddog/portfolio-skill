#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import bootstrap_database
from app.utils.cli import resolve_db_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 Stock & Finance 的 backend/portfolio.db 导入数据到 skill 数据库。")
    parser.add_argument(
        "--source-db",
        default=str(ROOT.parent / "backend" / "portfolio.db"),
        help="源数据库路径，默认 ../backend/portfolio.db",
    )
    parser.add_argument("--db-path", help="目标 SQLite 数据库路径，默认 data/portfolio.db 或环境变量 PORTFOLIO_DB_PATH")
    return parser.parse_args()


def connect_source(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def infer_account_market(account_type: str, account_currency: str) -> str:
    if account_type == "US_STOCK" or account_currency == "USD":
        return "US"
    if account_type in {"CN_STOCK", "FUND_PLATFORM"}:
        return "CN"
    return "CN"


def upsert_account(target: sqlite3.Connection, row: sqlite3.Row) -> int:
    market = infer_account_market(row["type"], row["currency"])
    existing = target.execute("SELECT id FROM accounts WHERE name = ?", (row["name"],)).fetchone()
    if existing:
        target.execute(
            """
            UPDATE accounts
            SET market = ?, base_currency = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (market, row["currency"], existing["id"]),
        )
        return int(existing["id"])

    cursor = target.execute(
        """
        INSERT INTO accounts (name, market, base_currency, is_active)
        VALUES (?, ?, ?, 1)
        """,
        (row["name"], market, row["currency"]),
    )
    return int(cursor.lastrowid)


def upsert_asset(target: sqlite3.Connection, row: sqlite3.Row) -> int:
    existing = target.execute(
        "SELECT id FROM assets WHERE symbol = ? AND market = ?",
        (row["symbol"], row["market"]),
    ).fetchone()
    if existing:
        target.execute(
            """
            UPDATE assets
            SET name = ?, asset_type = ?, currency = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (row["name"], row["asset_type"], row["currency"], row["is_active"], existing["id"]),
        )
        return int(existing["id"])

    cursor = target.execute(
        """
        INSERT INTO assets (
            symbol, market, name, asset_type, currency, is_active,
            last_price, last_price_date, last_price_source
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
        """,
        (row["symbol"], row["market"], row["name"], row["asset_type"], row["currency"], row["is_active"]),
    )
    return int(cursor.lastrowid)


def transaction_exists(target: sqlite3.Connection, account_id: int, asset_id: int, row: sqlite3.Row) -> bool:
    existing = target.execute(
        """
        SELECT id
        FROM transactions
        WHERE account_id = ?
          AND asset_id = ?
          AND trade_date = ?
          AND transaction_type = ?
          AND quantity = ?
          AND unit_price = ?
          AND gross_amount = ?
          AND fee = ?
          AND currency = ?
        LIMIT 1
        """,
        (
            account_id,
            asset_id,
            row["trade_date"],
            row["transaction_type"],
            str(row["quantity"]),
            str(row["unit_price"]),
            str(row["gross_amount"]),
            str(row["fee"]),
            row["currency"],
        ),
    ).fetchone()
    return existing is not None


def import_transactions(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    account_map: dict[int, int],
    asset_map: dict[int, int],
) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    rows = source.execute("SELECT * FROM transactions ORDER BY trade_date ASC, id ASC").fetchall()
    for row in rows:
        target_account_id = account_map[row["account_id"]]
        target_asset_id = asset_map[row["asset_id"]]
        if transaction_exists(target, target_account_id, target_asset_id, row):
            skipped += 1
            continue

        target.execute(
            """
            INSERT INTO transactions (
                trade_date, transaction_type, account_id, asset_id, quantity, unit_price,
                gross_amount, fee, currency, note, raw_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["trade_date"],
                row["transaction_type"],
                target_account_id,
                target_asset_id,
                str(row["quantity"]),
                str(row["unit_price"]),
                str(row["gross_amount"]),
                str(row["fee"]),
                row["currency"],
                row["note"],
                row["note"] or f"Imported from backend transaction #{row['id']}",
            ),
        )
        inserted += 1
    return inserted, skipped


def import_price_history(
    source: sqlite3.Connection,
    target: sqlite3.Connection,
    asset_map: dict[int, int],
) -> int:
    inserted_or_updated = 0
    rows = source.execute(
        "SELECT * FROM price_history ORDER BY asset_id ASC, price_date ASC, id ASC"
    ).fetchall()
    grouped: dict[int, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[int(row["asset_id"])].append(row)

    for source_asset_id, asset_rows in grouped.items():
        prev_close = None
        target_asset_id = asset_map[source_asset_id]
        for row in asset_rows:
            target.execute(
                """
                INSERT INTO price_history (
                    asset_id, price_date, close_price, prev_close_price, currency, source
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id, price_date, source) DO UPDATE SET
                    close_price = excluded.close_price,
                    prev_close_price = excluded.prev_close_price,
                    currency = excluded.currency
                """,
                (
                    target_asset_id,
                    row["price_date"],
                    str(row["close_price"]),
                    str(prev_close) if prev_close is not None else None,
                    row["currency"],
                    row["source"],
                ),
            )
            prev_close = row["close_price"]
            inserted_or_updated += 1

        latest = asset_rows[-1]
        target.execute(
            """
            UPDATE assets
            SET last_price = ?, last_price_date = ?, last_price_source = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (str(latest["close_price"]), latest["price_date"], latest["source"], target_asset_id),
        )

    return inserted_or_updated


def main() -> None:
    args = parse_args()
    target_db_path = resolve_db_path(args.db_path)
    source = connect_source(args.source_db)
    target = bootstrap_database(db_path=target_db_path)

    source_accounts = source.execute("SELECT * FROM accounts ORDER BY id ASC").fetchall()
    source_assets = source.execute("SELECT * FROM assets ORDER BY id ASC").fetchall()

    account_map: dict[int, int] = {}
    for row in source_accounts:
        account_map[int(row["id"])] = upsert_account(target, row)

    asset_map: dict[int, int] = {}
    for row in source_assets:
        asset_map[int(row["id"])] = upsert_asset(target, row)

    imported_transactions, skipped_transactions = import_transactions(source, target, account_map, asset_map)
    imported_prices = import_price_history(source, target, asset_map)

    target.commit()
    source.close()
    target.close()

    print("导入完成")
    print(f"- 源数据库: {args.source_db}")
    print(f"- 目标数据库: {target_db_path}")
    print(f"- 账户数: {len(account_map)}")
    print(f"- 标的数: {len(asset_map)}")
    print(f"- 新增交易数: {imported_transactions}")
    print(f"- 跳过重复交易数: {skipped_transactions}")
    print(f"- 导入或更新价格记录数: {imported_prices}")


if __name__ == "__main__":
    main()
