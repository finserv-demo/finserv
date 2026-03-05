"""FastAPI routes for the portfolio service."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from services.portfolio.db import (
    get_portfolio,
    get_portfolios_for_user,
    get_holdings_for_portfolio,
    get_transactions_for_portfolio,
    get_all_transactions_for_portfolio,
)
from services.portfolio.calculator import (
    calculate_portfolio_value,
    calculate_portfolio_drift,
    generate_rebalance_trades,
    execute_rebalance,
    get_portfolio_summary,
)
from services.portfolio.errors import (
    PortfolioNotFoundError,
    InvalidAllocationError,
    RebalanceError,
    InsufficientFundsError,
    MarketDataUnavailableError,
)

router = APIRouter()


# --- Request/Response schemas ---

class RebalanceRequest(BaseModel):
    portfolio_id: str
    dry_run: bool = False


class RebalanceResponse(BaseModel):
    portfolio_id: str
    status: str
    trades_count: int = 0
    trades: list = []


class AllocationUpdateRequest(BaseModel):
    portfolio_id: str
    allocations: dict[str, float]


# --- Routes ---

@router.get("/portfolios/{user_id}")
async def get_user_portfolios(user_id: str):
    """Get all portfolios for a user."""
    portfolios = get_portfolios_for_user(user_id)
    if not portfolios:
        raise HTTPException(status_code=404, detail=f"No portfolios found for user {user_id}")
    return {"portfolios": portfolios}


@router.get("/portfolio/{portfolio_id}")
async def get_portfolio_detail(portfolio_id: str):
    """Get detailed portfolio information including holdings."""
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

    holdings = get_holdings_for_portfolio(portfolio_id)
    return {
        "portfolio": portfolio,
        "holdings": holdings,
    }


@router.get("/portfolio/{portfolio_id}/value")
async def get_portfolio_value(portfolio_id: str):
    """Get current portfolio valuation."""
    try:
        return calculate_portfolio_value(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MarketDataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/portfolio/{portfolio_id}/drift")
async def get_drift(portfolio_id: str):
    """Get portfolio drift from target allocations."""
    try:
        return calculate_portfolio_drift(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rebalance")
async def rebalance_portfolio(request: RebalanceRequest):
    """Rebalance a portfolio to its target allocations.

    BUG: Returns 200 even on validation errors (e.g. invalid portfolio_id,
    missing allocations) — should return 422 for validation failures.
    """
    try:
        if request.dry_run:
            trades = generate_rebalance_trades(request.portfolio_id)
            return {
                "portfolio_id": request.portfolio_id,
                "status": "dry_run",
                "trades_count": len(trades),
                "trades": trades,
            }
        else:
            result = execute_rebalance(request.portfolio_id)
            # BUG: returns 200 even when there's a validation error
            return result

    except PortfolioNotFoundError:
        # BUG: should return 404, but returns 200 with error in body
        return {"portfolio_id": request.portfolio_id, "status": "error", "message": "Portfolio not found"}
    except InvalidAllocationError as e:
        # BUG: should return 422 for validation error
        return {"portfolio_id": request.portfolio_id, "status": "error", "message": str(e)}
    except RebalanceError as e:
        return {"portfolio_id": request.portfolio_id, "status": "error", "message": str(e)}


@router.get("/portfolio/{portfolio_id}/transactions")
async def get_transactions(
    portfolio_id: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="executed_at"),
    sort_order: str = Query(default="desc"),
):
    """Get paginated transactions for a portfolio.

    NOTE: The sort parameters are accepted but the page number doesn't persist
    correctly when sort is changed — it should reset to page 1 on sort change
    but currently the frontend has a bug where it doesn't.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

    transactions = get_transactions_for_portfolio(portfolio_id, page=page, per_page=per_page)

    # Sort by the specified field
    reverse = sort_order == "desc"
    try:
        transactions.sort(key=lambda t: t.get(sort_by, ""), reverse=reverse)
    except (TypeError, KeyError):
        pass  # silently ignore invalid sort fields — should return 400

    return {
        "portfolio_id": portfolio_id,
        "transactions": transactions,
        "page": page,
        "per_page": per_page,
        "total": len(get_transactions_for_portfolio(portfolio_id, page=1, per_page=999999)),
    }


@router.get("/portfolio/{portfolio_id}/history")
async def get_portfolio_history(portfolio_id: str):
    """Get full transaction history for a portfolio.

    WARNING: This endpoint has an N+1 query problem — it queries transactions
    per holding instead of doing a single query.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

    # This uses the N+1 pattern from db.py
    transactions = get_all_transactions_for_portfolio(portfolio_id)

    return {
        "portfolio_id": portfolio_id,
        "transactions": transactions,
        "total": len(transactions),
    }


@router.get("/portfolio/{portfolio_id}/summary")
async def portfolio_summary(portfolio_id: str):
    """Get a high-level portfolio summary."""
    try:
        # BUG: passing None for user — will fail if summary tries to access risk_profile
        summary = get_portfolio_summary(portfolio_id, user=None)
        return summary
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except MarketDataUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put("/portfolio/{portfolio_id}/allocations")
async def update_allocations(portfolio_id: str, request: AllocationUpdateRequest):
    """Update target allocations for a portfolio."""
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

    # Validate allocations sum to 100
    total = sum(request.allocations.values())
    if abs(total - 100.0) > 0.01:
        raise HTTPException(status_code=422, detail=f"Allocations must sum to 100%, got {total}%")

    from services.portfolio.db import update_portfolio
    update_portfolio(portfolio_id, {"target_allocations": request.allocations})

    return {"status": "updated", "portfolio_id": portfolio_id, "allocations": request.allocations}
