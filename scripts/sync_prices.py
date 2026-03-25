#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DEFAULT_PROVIDER
from app.db import bootstrap_database
from app.services.pricing import sync_prices
from app.utils.cli import resolve_db_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同步活跃标的的最新价格。")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help="价格源，支持 auto、yahoo、akshare、mock")
    parser.add_argument("--db-path", help="SQLite 数据库路径，默认 data/portfolio.db 或环境变量 PORTFOLIO_DB_PATH")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)
    conn = bootstrap_database(db_path=db_path)
    rows = sync_prices(conn=conn, provider_name=args.provider)
    conn.close()

    success_count = sum(1 for row in rows if row["status"] == "ok")
    error_count = sum(1 for row in rows if row["status"] == "error")
    print(f"已处理 {len(rows)} 个标的，成功 {success_count}，失败 {error_count}，价格源: {args.provider}")
    print(f"数据库: {db_path}")
    for row in rows:
        if row["status"] == "ok":
            print(
                f"- {row['symbol']} ({row['market']}): "
                f"{row['close_price']}，前收 {row['prev_close_price']}，日期 {row['price_date']}，来源 {row['source']}"
            )
        else:
            print(f"- {row['symbol']} ({row['market']}): 同步失败，原因 {row['error']}")


if __name__ == "__main__":
    main()
