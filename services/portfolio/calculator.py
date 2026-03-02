"""Portfolio calculation logic — valuations, drift, rebalancing."""

from datetime import datetime
from typing import Optional

from services.portfolio.db import (
    get_portfolio,
    get_holdings_for_portfolio,
    update_holding,
    update_portfolio,
    add_transaction,
    create_holding,
)
from services.portfolio.errors import (
    PortfolioNotFoundError,
    InvalidAllocationError,
    RebalanceError,
    MarketDataUnavailableError,
)


def calculate_portfolio_value(portfolio_id: str) -> dict:
    """Calculate the total value of a portfolio and per-holding breakdown.

    Returns dict with total_value, holdings_value, and cash_value.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)

    holdings = get_holdings_for_portfolio(portfolio_id)

    total_value = 0.0
    holdings_breakdown = []

    for holding in holdings:
        # BUG: no null check on current_price — will crash if market data hasn't loaded
        holding_value = holding["quantity"] * holding["current_price"]
        total_value += holding_value

        cost_basis = holding["quantity"] * holding["average_cost"]
        gain_loss = holding_value - cost_basis
        gain_loss_pct = (gain_loss / cost_basis) * 100  # BUG: division by zero if cost_basis is 0

        holdings_breakdown.append({
            "symbol": holding["symbol"],
            "name": holding["name"],
            "quantity": holding["quantity"],
            "current_price": holding["current_price"],
            "value": holding_value,
            "cost_basis": cost_basis,
            "gain_loss": gain_loss,
            "gain_loss_pct": round(gain_loss_pct, 2),
            "currency": "GBP",
        })

    return {
        "portfolio_id": portfolio_id,
        "total_value": round(total_value, 2),
        "holdings": holdings_breakdown,
        "currency": "GBP",
        "calculated_at": datetime.utcnow().isoformat(),
    }


def calculate_portfolio_drift(portfolio_id: str) -> dict:
    """Calculate how far a portfolio has drifted from its target allocations.

    Returns drift percentages per holding and total absolute drift.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)

    holdings = get_holdings_for_portfolio(portfolio_id)
    target_allocations = portfolio.get("target_allocations", {})

    if not target_allocations:
        return {"portfolio_id": portfolio_id, "total_drift_pct": 0.0, "holdings_drift": {}}

    # Calculate total portfolio value
    total_value = 0.0
    for holding in holdings:
        if holding["current_price"]:
            total_value += holding["quantity"] * holding["current_price"]

    if total_value == 0:
        return {"portfolio_id": portfolio_id, "total_drift_pct": 0.0, "holdings_drift": {}}

    # Calculate actual allocations and drift
    holdings_drift = {}
    total_drift = 0.0

    for holding in holdings:
        symbol = holding["symbol"]
        if holding["current_price"]:
            actual_pct = (holding["quantity"] * holding["current_price"]) / total_value * 100
        else:
            actual_pct = 0.0

        target_pct = target_allocations.get(symbol, 0.0)
        drift = actual_pct - target_pct
        holdings_drift[symbol] = round(drift, 2)
        total_drift += abs(drift)

    # Check for target allocations with no corresponding holdings
    for symbol, target_pct in target_allocations.items():
        if symbol not in holdings_drift:
            holdings_drift[symbol] = round(-target_pct, 2)
            total_drift += target_pct

    return {
        "portfolio_id": portfolio_id,
        "total_drift_pct": round(total_drift, 2),
        "holdings_drift": holdings_drift,
        "calculated_at": datetime.utcnow().isoformat(),
    }


def generate_rebalance_trades(portfolio_id: str) -> list[dict]:
    """Generate the trades needed to rebalance a portfolio to target allocations.

    BUG: This rounds share quantities DOWN using int(), which means the portfolio
    never quite reaches its target allocation. Over time, this causes permanent drift
    as fractional remainders accumulate.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)

    holdings = get_holdings_for_portfolio(portfolio_id)
    target_allocations = portfolio.get("target_allocations", {})

    if not target_allocations:
        raise RebalanceError("No target allocations defined")

    # Validate allocations sum to 100
    total_target = sum(target_allocations.values())
    if abs(total_target - 100.0) > 0.01:
        raise InvalidAllocationError(total_target)

    # Calculate total portfolio value
    total_value = 0.0
    holdings_map = {}
    for holding in holdings:
        if holding["current_price"] is None:
            raise MarketDataUnavailableError(holding["symbol"])
        value = holding["quantity"] * holding["current_price"]
        total_value += value
        holdings_map[holding["symbol"]] = holding

    if total_value == 0:
        raise RebalanceError("Portfolio has zero value")

    trades = []

    for symbol, target_pct in target_allocations.items():
        if symbol == "CASH":
            continue  # skip cash allocation for now

        target_value = total_value * (target_pct / 100.0)
        holding = holdings_map.get(symbol)

        if holding:
            current_value = holding["quantity"] * holding["current_price"]
            diff_value = target_value - current_value

            if abs(diff_value) < 10.0:  # skip tiny trades
                continue

            # BUG: int() truncates fractional shares — should use Decimal and proper rounding
            quantity = int(abs(diff_value) / holding["current_price"])

            if quantity == 0:
                continue

            trade_type = "BUY" if diff_value > 0 else "SELL"
            trades.append({
                "symbol": symbol,
                "trade_type": trade_type,
                "quantity": quantity,  # always integer — loses fractional amounts
                "estimated_price": holding["current_price"],
                "estimated_value": round(quantity * holding["current_price"], 2),
            })
        else:
            # New holding needed
            # Need to fetch price somehow — for now just skip
            # BUG: we just silently skip symbols that have no existing holding
            pass

    return trades


def execute_rebalance(portfolio_id: str) -> dict:
    """Execute a rebalance by generating and applying trades.

    Returns a summary of trades executed.
    """
    trades = generate_rebalance_trades(portfolio_id)

    if not trades:
        return {
            "portfolio_id": portfolio_id,
            "status": "no_trades_needed",
            "trades": [],
        }

    executed_trades = []
    for trade in trades:
        symbol = trade["symbol"]
        quantity = trade["quantity"]
        price = trade["estimated_price"]

        # Record the transaction
        txn = add_transaction({
            "portfolio_id": portfolio_id,
            "symbol": symbol,
            "transaction_type": trade["trade_type"],
            "quantity": quantity,
            "price": price,
            "total_amount": round(quantity * price, 2),
            "currency": "GBP",
            "executed_at": datetime.utcnow(),
            "settled": False,
        })

        # Update holding quantity
        holdings = get_holdings_for_portfolio(portfolio_id)
        holding = next((h for h in holdings if h["symbol"] == symbol), None)

        if holding:
            if trade["trade_type"] == "BUY":
                new_qty = holding["quantity"] + quantity
                # Update average cost
                total_cost = (holding["quantity"] * holding["average_cost"]) + (quantity * price)
                new_avg_cost = total_cost / new_qty
                update_holding(holding["id"], {
                    "quantity": new_qty,
                    "average_cost": round(new_avg_cost, 4),
                })
            else:
                new_qty = holding["quantity"] - quantity
                update_holding(holding["id"], {"quantity": max(0, new_qty)})

        executed_trades.append({
            "transaction_id": txn["id"],
            "symbol": symbol,
            "trade_type": trade["trade_type"],
            "quantity": quantity,
            "price": price,
            "total": round(quantity * price, 2),
        })

    # Update last rebalanced timestamp
    update_portfolio(portfolio_id, {"last_rebalanced": datetime.utcnow()})

    return {
        "portfolio_id": portfolio_id,
        "status": "completed",
        "trades_count": len(executed_trades),
        "trades": executed_trades,
    }


def calculate_daily_pnl(portfolio_id: str) -> dict:
    """Calculate daily P&L for a portfolio.

    NOTE: This is a simplified version — in production, we'd compare
    against yesterday's closing prices from market data service.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise PortfolioNotFoundError(portfolio_id)

    holdings = get_holdings_for_portfolio(portfolio_id)

    total_pnl = 0.0
    holdings_pnl = []

    for holding in holdings:
        # Simulate daily change — in reality we'd call market-data service
        # BUG: using hardcoded 0.5% daily change instead of real data
        daily_change_pct = 0.5
        current_value = holding["quantity"] * holding["current_price"]
        daily_pnl = current_value * (daily_change_pct / 100)

        total_pnl += daily_pnl
        holdings_pnl.append({
            "symbol": holding["symbol"],
            "daily_pnl": round(daily_pnl, 2),
            "daily_change_pct": daily_change_pct,
        })

    return {
        "portfolio_id": portfolio_id,
        "total_daily_pnl": round(total_pnl, 2),
        "holdings": holdings_pnl,
        "currency": "GBP",
    }


def get_portfolio_summary(portfolio_id: str, user: Optional[dict] = None) -> dict:
    """Get a high-level portfolio summary.

    BUG: Accesses user.risk_profile without null check — will crash with AttributeError
    if user has no risk profile set (e.g. first login before completing questionnaire).
    """
    valuation = calculate_portfolio_value(portfolio_id)
    drift = calculate_portfolio_drift(portfolio_id)
    pnl = calculate_daily_pnl(portfolio_id)

    portfolio = get_portfolio(portfolio_id)

    summary = {
        "portfolio_id": portfolio_id,
        "account_type": portfolio["account_type"],
        "total_value": valuation["total_value"],
        "daily_pnl": pnl["total_daily_pnl"],
        "total_drift_pct": drift["total_drift_pct"],
        "holdings_count": len(valuation["holdings"]),
        "last_rebalanced": portfolio.get("last_rebalanced"),
        "currency": "GBP",
    }

    # BUG: no null check — user might be None or risk_profile might be None
    if user:
        summary["risk_level"] = user["risk_profile"]["risk_level"]

    return summary
