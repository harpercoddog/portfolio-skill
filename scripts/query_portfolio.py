#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import bootstrap_database
from app.services.portfolio import build_positions, summarize_positions
from app.utils.formatting import render_position_line
from app.utils.money import format_decimal, format_percent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="查询组合持仓。")
    parser.add_argument("--account", help="按账户过滤")
    parser.add_argument("--symbol", help="按标的过滤")
    parser.add_argument("--include-zero", action="store_true", help="包含已清仓标的")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = bootstrap_database()
    positions = build_positions(
        conn=conn,
        account_name=args.account,
        symbol=args.symbol,
        include_zero=args.include_zero,
    )
    summary = summarize_positions(positions)
    conn.close()

    scope_parts = []
    if args.account:
        scope_parts.append(f"账户={args.account}")
    if args.symbol:
        scope_parts.append(f"标的={args.symbol.upper()}")
    scope = "，".join(scope_parts) if scope_parts else "全部账户"

    print(f"查询范围: {scope}")
    print(f"持仓数量: {summary['position_count']}")
    print(f"总成本: {format_decimal(summary['total_cost_basis'])}")
    print(f"总市值: {format_decimal(summary['total_market_value'])}")
    print(f"总浮盈浮亏: {format_decimal(summary['total_unrealized_pnl'])}")
    print(f"总已实现收益: {format_decimal(summary['total_realized_pnl'])}")
    print(f"总收益率: {format_percent(summary['total_return_rate'])}")
    print("持仓明细:")
    if not positions:
        print("- 当前没有符合条件的持仓。")
        return
    for position in positions:
        print(render_position_line(position))


if __name__ == "__main__":
    main()

