from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date

from app.models import PositionState, TransactionType
from app.utils.money import quant_money, quant_qty, safe_divide, to_decimal


def latest_price_rows(conn: sqlite3.Connection) -> dict[int, sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT *
        FROM price_history
        ORDER BY asset_id ASC, price_date DESC, id DESC
        """
    ).fetchall()
    latest: dict[int, sqlite3.Row] = {}
    for row in rows:
        if row["asset_id"] not in latest:
            latest[row["asset_id"]] = row
    return latest


def _apply_transaction(state: PositionState, row: sqlite3.Row) -> PositionState:
    tx_type = TransactionType(row["transaction_type"])
    quantity = to_decimal(row["quantity"])
    unit_price = to_decimal(row["unit_price"])
    gross_amount = to_decimal(row["gross_amount"])
    fee = to_decimal(row["fee"])

    if tx_type in {TransactionType.BUY, TransactionType.MANUAL_OPENING_POSITION}:
        new_total_cost = state.quantity * state.average_cost + gross_amount + fee
        new_quantity = state.quantity + quantity
        state.quantity = quant_qty(new_quantity)
        state.total_cost_basis = quant_money(new_total_cost)
        state.average_cost = quant_money(new_total_cost / new_quantity) if new_quantity > 0 else quant_money(0)
        return state

    if tx_type == TransactionType.TRANSFER_IN:
        transfer_cost = quantity * unit_price + fee
        new_total_cost = state.quantity * state.average_cost + transfer_cost
        new_quantity = state.quantity + quantity
        state.quantity = quant_qty(new_quantity)
        state.total_cost_basis = quant_money(new_total_cost)
        state.average_cost = quant_money(new_total_cost / new_quantity) if new_quantity > 0 else quant_money(0)
        return state

    if tx_type == TransactionType.SELL:
        if quantity > state.quantity:
            raise ValueError(f"卖出数量超过当前持仓: {row['transaction_type']} #{row['id']}")
        realized = gross_amount - fee - state.average_cost * quantity
        state.realized_pnl = quant_money(state.realized_pnl + realized)
        remaining_quantity = state.quantity - quantity
        state.quantity = quant_qty(remaining_quantity)
        if remaining_quantity <= 0:
            state.average_cost = quant_money(0)
            state.total_cost_basis = quant_money(0)
        else:
            state.total_cost_basis = quant_money(remaining_quantity * state.average_cost)
        return state

    if tx_type == TransactionType.TRANSFER_OUT:
        if quantity > state.quantity:
            raise ValueError(f"转出数量超过当前持仓: {row['transaction_type']} #{row['id']}")
        remaining_quantity = state.quantity - quantity
        state.quantity = quant_qty(remaining_quantity)
        state.realized_pnl = quant_money(state.realized_pnl - fee)
        if remaining_quantity <= 0:
            state.average_cost = quant_money(0)
            state.total_cost_basis = quant_money(0)
        else:
            state.total_cost_basis = quant_money(remaining_quantity * state.average_cost)
        return state

    if tx_type == TransactionType.DIVIDEND:
        state.realized_pnl = quant_money(state.realized_pnl + gross_amount - fee)
        return state

    raise ValueError(f"不支持的交易类型: {row['transaction_type']}")


def build_positions(
    conn: sqlite3.Connection,
    account_name: str | None = None,
    symbol: str | None = None,
    include_zero: bool = False,
) -> list[dict]:
    where = []
    params: list[str] = []
    if account_name:
        where.append("acc.name = ?")
        params.append(account_name)
    if symbol:
        where.append("ast.symbol = ?")
        params.append(symbol.upper())

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""
    tx_rows = conn.execute(
        f"""
        SELECT
            tx.*,
            acc.name AS account_name,
            acc.market AS account_market,
            ast.symbol AS symbol,
            ast.market AS market,
            ast.currency AS asset_currency
        FROM transactions tx
        JOIN accounts acc ON acc.id = tx.account_id
        JOIN assets ast ON ast.id = tx.asset_id
        {where_clause}
        ORDER BY acc.name ASC, ast.symbol ASC, tx.trade_date ASC, tx.id ASC
        """,
        params,
    ).fetchall()

    grouped: dict[tuple[int, int], list[sqlite3.Row]] = defaultdict(list)
    for row in tx_rows:
        grouped[(row["account_id"], row["asset_id"])].append(row)

    latest_prices = latest_price_rows(conn)
    positions: list[dict] = []
    for rows in grouped.values():
        state = PositionState()
        for row in rows:
            state = _apply_transaction(state, row)

        if state.quantity <= 0 and not include_zero:
            continue

        sample = rows[-1]
        latest_price = latest_prices.get(sample["asset_id"])
        current_price = to_decimal(latest_price["close_price"]) if latest_price else None
        prev_close_price = to_decimal(latest_price["prev_close_price"]) if latest_price and latest_price["prev_close_price"] else None
        market_value = quant_money(state.quantity * current_price) if current_price is not None else None
        unrealized_pnl = (
            quant_money((current_price - state.average_cost) * state.quantity)
            if current_price is not None
            else None
        )
        total_pnl = quant_money(state.realized_pnl + unrealized_pnl) if unrealized_pnl is not None else None
        return_rate = safe_divide(total_pnl, state.total_cost_basis) if total_pnl is not None else None
        day_change_pct = (
            safe_divide(current_price - prev_close_price, prev_close_price)
            if current_price is not None and prev_close_price is not None and prev_close_price != 0
            else None
        )

        positions.append(
            {
                "account_name": sample["account_name"],
                "symbol": sample["symbol"],
                "market": sample["market"],
                "currency": sample["asset_currency"],
                "quantity": state.quantity,
                "average_cost": state.average_cost,
                "total_cost_basis": state.total_cost_basis,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "realized_pnl": state.realized_pnl,
                "total_pnl": total_pnl,
                "return_rate": return_rate,
                "price_date": latest_price["price_date"] if latest_price else None,
                "prev_close_price": prev_close_price,
                "day_change_pct": day_change_pct,
            }
        )

    positions.sort(key=lambda item: (item["account_name"], item["symbol"]))
    return positions


def summarize_positions(positions: list[dict]) -> dict:
    total_cost = quant_money(sum((item["total_cost_basis"] for item in positions), start=to_decimal(0)))
    total_market_value = quant_money(
        sum((item["market_value"] or to_decimal(0) for item in positions), start=to_decimal(0))
    )
    total_unrealized = quant_money(
        sum((item["unrealized_pnl"] or to_decimal(0) for item in positions), start=to_decimal(0))
    )
    total_realized = quant_money(sum((item["realized_pnl"] for item in positions), start=to_decimal(0)))
    return {
        "position_count": len(positions),
        "total_cost_basis": total_cost,
        "total_market_value": total_market_value,
        "total_unrealized_pnl": total_unrealized,
        "total_realized_pnl": total_realized,
        "total_return_rate": safe_divide(total_unrealized + total_realized, total_cost),
    }


def summarize_by_account(positions: list[dict]) -> list[dict]:
    buckets: dict[str, dict] = {}
    for position in positions:
        bucket = buckets.setdefault(
            position["account_name"],
            {
                "account_name": position["account_name"],
                "market_value": to_decimal(0),
                "unrealized_pnl": to_decimal(0),
                "realized_pnl": to_decimal(0),
            },
        )
        bucket["market_value"] += position["market_value"] or to_decimal(0)
        bucket["unrealized_pnl"] += position["unrealized_pnl"] or to_decimal(0)
        bucket["realized_pnl"] += position["realized_pnl"]

    return [
        {
            "account_name": account_name,
            "market_value": quant_money(payload["market_value"]),
            "unrealized_pnl": quant_money(payload["unrealized_pnl"]),
            "realized_pnl": quant_money(payload["realized_pnl"]),
        }
        for account_name, payload in sorted(buckets.items(), key=lambda item: item[0])
    ]
