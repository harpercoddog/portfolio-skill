#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import bootstrap_database
from app.services.transactions import record_trade
from app.utils.cli import resolve_db_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="通过自然语言记录一笔交易。")
    parser.add_argument("--text", required=True, help="交易描述，例如：买入 AAPL 10 股，价格 210，账户是美股账户")
    parser.add_argument("--trade-date", help="交易日期，格式 YYYY-MM-DD，默认今天")
    parser.add_argument("--db-path", help="SQLite 数据库路径，默认 data/portfolio.db 或环境变量 PORTFOLIO_DB_PATH")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    trade_date = date.fromisoformat(args.trade_date) if args.trade_date else None
    db_path = resolve_db_path(args.db_path)
    conn = bootstrap_database(db_path=db_path)
    result = record_trade(conn=conn, text=args.text, trade_date=trade_date)
    conn.close()

    print("交易已记录")
    print(f"- 数据库: {db_path}")
    print(f"- ID: {result['transaction_id']}")
    print(f"- 日期: {result['trade_date']}")
    print(f"- 类型: {result['transaction_type']}")
    print(f"- 账户: {result['account_name']}")
    print(f"- 标的: {result['symbol']} ({result['market']})")
    print(f"- 数量: {result['quantity']}")
    print(f"- 价格: {result['unit_price']}")
    print(f"- 金额: {result['gross_amount']} {result['currency']}")
    print(f"- 手续费: {result['fee']} {result['currency']}")


if __name__ == "__main__":
    main()
