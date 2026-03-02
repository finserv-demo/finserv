"""Database setup and helpers for the portfolio service."""

import uuid
from datetime import datetime
from typing import Optional

# In-memory database for demo purposes
_portfolios: dict = {}
_holdings: dict = {}
_transactions: list = []


async def init_db():
    """Initialize the database with some sample data."""
    # Create sample portfolios
    sample_user_id = "user_001"

    portfolio_id = "pf_001"
    _portfolios[portfolio_id] = {
        "id": portfolio_id,
        "user_id": sample_user_id,
        "account_type": "ISA",
        "target_allocations": {
            "VWRL.L": 40.0,
            "VGOV.L": 30.0,
            "VUKE.L": 20.0,
            "CASH": 10.0,
        },
        "created_at": datetime(2024, 1, 15, 10, 30, 0),
        "last_rebalanced": datetime(2024, 11, 1, 9, 0, 0),
    }

    # Sample holdings
    _holdings["h_001"] = {
        "id": "h_001",
        "portfolio_id": portfolio_id,
        "symbol": "VWRL.L",
        "name": "Vanguard FTSE All-World ETF",
        "quantity": 150.0,
        "average_cost": 78.50,
        "current_price": 82.30,
        "currency": "GBP",
    }
    _holdings["h_002"] = {
        "id": "h_002",
        "portfolio_id": portfolio_id,
        "symbol": "VGOV.L",
        "name": "Vanguard UK Government Bond ETF",
        "quantity": 200.0,
        "average_cost": 21.10,
        "current_price": 20.85,
        "currency": "GBP",
    }
    _holdings["h_003"] = {
        "id": "h_003",
        "portfolio_id": portfolio_id,
        "symbol": "VUKE.L",
        "name": "Vanguard FTSE 100 ETF",
        "quantity": 100.0,
        "average_cost": 32.40,
        "current_price": 33.15,
        "currency": "GBP",
    }

    # Sample transactions
    _transactions.extend([
        {
            "id": "tx_001",
            "portfolio_id": portfolio_id,
            "symbol": "VWRL.L",
            "transaction_type": "BUY",
            "quantity": 50.0,
            "price": 78.50,
            "total_amount": 3925.00,
            "currency": "GBP",
            "executed_at": datetime(2024, 1, 20, 14, 30, 0),
            "settled": True,
        },
        {
            "id": "tx_002",
            "portfolio_id": portfolio_id,
            "symbol": "VGOV.L",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price": 21.10,
            "total_amount": 2110.00,
            "currency": "GBP",
            "executed_at": datetime(2024, 2, 5, 11, 15, 0),
            "settled": True,
        },
        {
            "id": "tx_003",
            "portfolio_id": portfolio_id,
            "symbol": "VWRL.L",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price": 78.50,
            "total_amount": 7850.00,
            "currency": "GBP",
            "executed_at": datetime(2024, 3, 10, 9, 45, 0),
            "settled": True,
        },
        {
            "id": "tx_004",
            "portfolio_id": portfolio_id,
            "symbol": "VUKE.L",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price": 32.40,
            "total_amount": 3240.00,
            "currency": "GBP",
            "executed_at": datetime(2024, 4, 15, 10, 0, 0),
            "settled": True,
        },
        {
            "id": "tx_005",
            "portfolio_id": portfolio_id,
            "symbol": "VGOV.L",
            "transaction_type": "BUY",
            "quantity": 100.0,
            "price": 21.10,
            "total_amount": 2110.00,
            "currency": "GBP",
            "executed_at": datetime(2024, 5, 20, 13, 30, 0),
            "settled": True,
        },
    ])

    # Create a GIA portfolio too
    gia_id = "pf_002"
    _portfolios[gia_id] = {
        "id": gia_id,
        "user_id": sample_user_id,
        "account_type": "GIA",
        "target_allocations": {
            "VWRL.L": 60.0,
            "VGOV.L": 25.0,
            "CASH": 15.0,
        },
        "created_at": datetime(2024, 3, 1, 12, 0, 0),
        "last_rebalanced": None,
    }


def get_portfolio(portfolio_id: str) -> Optional[dict]:
    return _portfolios.get(portfolio_id)


def get_portfolios_for_user(user_id: str) -> list[dict]:
    return [p for p in _portfolios.values() if p["user_id"] == user_id]


def get_holdings_for_portfolio(portfolio_id: str) -> list[dict]:
    return [h for h in _holdings.values() if h["portfolio_id"] == portfolio_id]


def get_holding(holding_id: str) -> Optional[dict]:
    return _holdings.get(holding_id)


def get_transactions_for_portfolio(portfolio_id: str, page: int = 1, per_page: int = 20) -> list[dict]:
    """Get paginated transactions for a portfolio.

    BUG: N+1 query pattern — in a real DB this would be one query per holding
    to get latest price, then another for the transactions themselves.
    """
    portfolio_txns = [t for t in _transactions if t["portfolio_id"] == portfolio_id]

    # Sort by date descending
    portfolio_txns.sort(key=lambda t: t["executed_at"], reverse=True)

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    return portfolio_txns[start:end]


def get_all_transactions_for_portfolio(portfolio_id: str) -> list[dict]:
    """Get ALL transactions for a portfolio (no pagination).

    Used by the history endpoint — this is the N+1 query problem:
    for each holding we make a separate "query" instead of a single joined query.
    """
    result = []
    holdings = get_holdings_for_portfolio(portfolio_id)

    # BUG: N+1 pattern — iterating holdings and filtering transactions per holding
    for holding in holdings:
        holding_txns = [
            t for t in _transactions
            if t["portfolio_id"] == portfolio_id and t["symbol"] == holding["symbol"]
        ]
        result.extend(holding_txns)

    return result


def add_transaction(transaction: dict) -> dict:
    transaction["id"] = f"tx_{uuid.uuid4().hex[:8]}"
    _transactions.append(transaction)
    return transaction


def update_holding(holding_id: str, updates: dict) -> Optional[dict]:
    if holding_id in _holdings:
        _holdings[holding_id].update(updates)
        return _holdings[holding_id]
    return None


def create_holding(holding: dict) -> dict:
    holding["id"] = f"h_{uuid.uuid4().hex[:8]}"
    _holdings[holding["id"]] = holding
    return holding


def update_portfolio(portfolio_id: str, updates: dict) -> Optional[dict]:
    if portfolio_id in _portfolios:
        _portfolios[portfolio_id].update(updates)
        return _portfolios[portfolio_id]
    return None
