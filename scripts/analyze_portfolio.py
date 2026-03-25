#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import bootstrap_database
from app.services.analytics import analyze_portfolio
from app.utils.cli import resolve_db_path
from app.utils.formatting import render_account_line
from app.utils.money import format_decimal, format_percent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成规则型组合分析报告。")
    parser.add_argument("--drop-threshold", type=float, default=0.05, help="单日跌幅提醒阈值，默认 0.05")
    parser.add_argument("--concentration-threshold", type=float, default=0.35, help="单一标的集中度阈值，默认 0.35")
    parser.add_argument("--pnl-threshold", type=float, default=0.20, help="浮盈浮亏提醒阈值，默认 0.20")
    parser.add_argument("--db-path", help="SQLite 数据库路径，默认 data/portfolio.db 或环境变量 PORTFOLIO_DB_PATH")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = resolve_db_path(args.db_path)
    conn = bootstrap_database(db_path=db_path)
    report = analyze_portfolio(
        conn=conn,
        drop_threshold=args.drop_threshold,
        concentration_threshold=args.concentration_threshold,
        pnl_threshold=args.pnl_threshold,
    )
    conn.close()

    summary = report["summary"]
    print("组合分析报告")
    print(f"- 数据库: {db_path}")
    print(f"- 汇总币种: {summary['report_currency']}")
    print(f"- 总市值: {format_decimal(summary['total_market_value'])} {summary['report_currency']}")
    print(f"- 总浮盈浮亏: {format_decimal(summary['total_unrealized_pnl'])} {summary['report_currency']}")
    print(f"- 总已实现收益: {format_decimal(summary['total_realized_pnl'])} {summary['report_currency']}")
    print(f"- 总收益率: {format_percent(summary['total_return_rate'])}")
    print("账户分布:")
    for row in report["account_breakdown"]:
        print(render_account_line(row, summary["total_market_value"]))
    print("前五大持仓:")
    for row in report["top_holdings"]:
        print(
            f"- {row['symbol']} / {row['account_name']}: 原币市值 {format_decimal(row['market_value'])} {row['currency']}，"
            f"折合市值 {format_decimal(row['market_value_base'])} {summary['report_currency']}，"
            f"收益率 {format_percent(row['return_rate'])}"
        )
    print("当日波动较大的标的:")
    if not report["big_movers"]:
        print("- 暂无可用的日波动数据。")
    for row in report["big_movers"]:
        print(
            f"- {row['symbol']}: 单日涨跌 {format_percent(row['day_change_pct'])}，"
            f"现价 {format_decimal(row['current_price'])}，前收 {format_decimal(row['prev_close_price'])}"
        )
    print("规则提醒:")
    for alert in report["alerts"]:
        print(f"- {alert}")


if __name__ == "__main__":
    main()
