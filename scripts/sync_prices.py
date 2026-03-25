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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="同步活跃标的的最新价格。")
    parser.add_argument("--provider", default=DEFAULT_PROVIDER, help="价格源，默认 mock")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = bootstrap_database()
    rows = sync_prices(conn=conn, provider_name=args.provider)
    conn.close()

    print(f"已同步 {len(rows)} 个标的，价格源: {args.provider}")
    for row in rows:
        print(
            f"- {row['symbol']} ({row['market']}): "
            f"{row['close_price']}，前收 {row['prev_close_price']}，日期 {row['price_date']}，来源 {row['source']}"
        )


if __name__ == "__main__":
    main()

