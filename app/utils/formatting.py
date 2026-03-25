from __future__ import annotations

from app.utils.money import format_decimal, format_percent


def render_position_line(position: dict) -> str:
    native_currency = position["currency"]
    report_suffix = ""
    if native_currency != "CNY":
        report_suffix = (
            f"，折合市值 {format_decimal(position['market_value_base'])} CNY"
            f"，折合浮盈浮亏 {format_decimal(position['unrealized_pnl_base'])} CNY"
        )
    return (
        f"- {position['account_name']} / {position['symbol']} ({position['market']}): "
        f"数量 {format_decimal(position['quantity'])}，"
        f"成本 {format_decimal(position['average_cost'])} {native_currency}，"
        f"现价 {format_decimal(position['current_price'])} {native_currency}，"
        f"市值 {format_decimal(position['market_value'])} {native_currency}，"
        f"浮盈浮亏 {format_decimal(position['unrealized_pnl'])} {native_currency}，"
        f"收益率 {format_percent(position['return_rate'])}"
        f"{report_suffix}"
    )


def render_account_line(summary: dict, total_market_value) -> str:
    weight = "N/A"
    if total_market_value:
        weight = format_percent(summary["market_value"] / total_market_value)
    return (
        f"- {summary['account_name']}: 市值 {format_decimal(summary['market_value'])} {summary.get('report_currency', 'CNY')}，"
        f"浮盈浮亏 {format_decimal(summary['unrealized_pnl'])} {summary.get('report_currency', 'CNY')}，"
        f"占比 {weight}"
    )
