from __future__ import annotations

import sqlite3

from app.config import BASE_CURRENCY
from app.services.portfolio import build_positions, summarize_by_account, summarize_positions
from app.utils.money import quant_money, safe_divide, to_decimal


def analyze_portfolio(
    conn: sqlite3.Connection,
    drop_threshold: float = 0.05,
    concentration_threshold: float = 0.35,
    pnl_threshold: float = 0.20,
) -> dict:
    positions = build_positions(conn=conn)
    summary = summarize_positions(positions)
    account_breakdown = summarize_by_account(positions)
    total_market_value = summary["total_market_value"]

    top_holdings = sorted(
        positions,
        key=lambda item: item["market_value_base"] or to_decimal(0),
        reverse=True,
    )[:5]
    big_movers = sorted(
        [item for item in positions if item["day_change_pct"] is not None],
        key=lambda item: abs(item["day_change_pct"]),
        reverse=True,
    )[:5]

    alerts: list[str] = []
    for position in positions:
        if position["current_price"] is None:
            alerts.append(f"{position['symbol']} 缺少最新价格，建议先执行 sync_prices。")
            continue

        if position["day_change_pct"] is not None and position["day_change_pct"] <= -to_decimal(drop_threshold):
            alerts.append(
                f"{position['symbol']} 单日跌幅 {position['day_change_pct']:.2%}，超过阈值，建议复盘最近的基本面或消息面。"
            )

        holding_weight = safe_divide(position["market_value_base"], total_market_value) if total_market_value > 0 else None
        if holding_weight is not None and holding_weight >= to_decimal(concentration_threshold):
            alerts.append(
                f"{position['symbol']} 占组合市值 {holding_weight:.2%}，集中度偏高，建议关注单一标的风险。"
            )

        pnl_ratio = safe_divide(position["unrealized_pnl"], position["total_cost_basis"])
        if pnl_ratio is not None and abs(pnl_ratio) >= to_decimal(pnl_threshold):
            direction = "浮盈" if pnl_ratio > 0 else "浮亏"
            alerts.append(f"{position['symbol']} {direction}比例 {pnl_ratio:.2%}，建议确认止盈止损规则是否仍然适用。")

    if not alerts:
        alerts.append("当前组合未触发规则提醒。")

    return {
        "summary": summary,
        "account_breakdown": account_breakdown,
        "top_holdings": top_holdings,
        "big_movers": big_movers,
        "alerts": alerts,
        "positions": positions,
        "total_market_value": quant_money(total_market_value),
        "total_unrealized_pnl": quant_money(summary["total_unrealized_pnl"]),
        "report_currency": BASE_CURRENCY,
    }
