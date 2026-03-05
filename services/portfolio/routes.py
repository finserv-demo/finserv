"""FastAPI routes for the portfolio service."""


from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.portfolio.calculator import (
    calculate_portfolio_drift,
    calculate_portfolio_value,
    execute_rebalance,
    generate_rebalance_trades,
    get_portfolio_summary,
)
from services.portfolio.db import (
    get_all_transactions_for_portfolio,
    get_holdings_for_portfolio,
    get_portfolio,
    get_portfolios_for_user,
    get_transactions_for_portfolio,
)
from services.portfolio.errors import (
    InvalidAllocationError,
    PortfolioNotFoundError,
    RebalanceError,
)

router = APIRouter()


# --- Request/Response schemas ---

class RebalanceRequest(BaseModel):
    """Request to rebalance a portfolio."""
    portfolio_id: str = Field(description="ID of the portfolio to rebalance", examples=["pf_001"])
    dry_run: bool = Field(
        default=False, description="If true, return proposed trades without executing", examples=[True]
    )


class RebalanceResponse(BaseModel):
    """Result of a rebalance operation."""
    portfolio_id: str = Field(description="ID of the rebalanced portfolio", examples=["pf_001"])
    status: str = Field(description="Rebalance status", examples=["completed"])
    trades_count: int = Field(default=0, description="Number of trades executed or proposed", examples=[3])
    trades: list = Field(default=[], description="List of trade details")


class AllocationUpdateRequest(BaseModel):
    """Request to update target allocations for a portfolio."""
    portfolio_id: str = Field(description="ID of the portfolio to update", examples=["pf_001"])
    allocations: dict[str, float] = Field(
        description="Target allocation percentages keyed by symbol (must sum to 100)",
        examples=[{"VWRL.L": 60.0, "VGOV.L": 40.0}],
    )


# --- Routes ---

@router.get("/portfolios/{user_id}", tags=["Portfolio - Holdings"], summary="Get all portfolios for a user")
async def get_user_portfolios(user_id: str):
    """Get all portfolios for a user.

    Returns a list of portfolio objects belonging to the specified user.
    """
    portfolios = get_portfolios_for_user(user_id)
    if not portfolios:
        raise HTTPException(status_code=404, detail=f"No portfolios found for user {user_id}")
    return {"portfolios": portfolios}


@router.get("/portfolio/{portfolio_id}", tags=["Portfolio - Holdings"], summary="Get portfolio detail with holdings")
async def get_portfolio_detail(portfolio_id: str):
    """Get detailed portfolio information including holdings.

    Returns the portfolio metadata along with a full list of current holdings.
    """
    portfolio = get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail=f"Portfolio {portfolio_id} not found")

    holdings = get_holdings_for_portfolio(portfolio_id)
    return {
        "portfolio": portfolio,
        "holdings": holdings,
    }


@router.get("/portfolio/{portfolio_id}/value", tags=["Portfolio - Holdings"], summary="Get current portfolio valuation")
async def get_portfolio_value(portfolio_id: str):
    """Get current portfolio valuation.

    Calculates the total value of a portfolio based on latest market prices.
    """
    try:
        return calculate_portfolio_value(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/portfolio/{portfolio_id}/drift",
    tags=["Portfolio - Rebalancing"],
    summary="Get portfolio drift from targets",
)
async def get_drift(portfolio_id: str):
    """Get portfolio drift from target allocations.

    Compares current holding weights to target allocations and returns
    the per-holding and total drift percentages.
    """
    try:
        return calculate_portfolio_drift(portfolio_id)
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rebalance", tags=["Portfolio - Rebalancing"], summary="Rebalance portfolio to target allocations")
async def rebalance_portfolio(request: RebalanceRequest):
    """Rebalance a portfolio to its target allocations.

    In dry-run mode, returns the proposed trades without executing.
    In live mode, executes the trades and returns the results.

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


@router.get(
    "/portfolio/{portfolio_id}/transactions",
    tags=["Portfolio - Transactions"],
    summary="Get paginated transactions",
)
async def get_transactions(
    portfolio_id: str,
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(default=20, ge=1, le=100, description="Number of transactions per page"),
    sort_by: str = Query(default="executed_at", description="Field to sort by"),
    sort_order: str = Query(default="desc", description="Sort direction: 'asc' or 'desc'"),
):
    """Get paginated transactions for a portfolio.

    Returns a paginated list of transactions with sorting support.

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


@router.get(
    "/portfolio/{portfolio_id}/history",
    tags=["Portfolio - Transactions"],
    summary="Get full transaction history",
)
async def get_portfolio_history(portfolio_id: str):
    """Get full transaction history for a portfolio.

    Returns every transaction for the portfolio without pagination.

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


@router.get("/portfolio/{portfolio_id}/summary", tags=["Portfolio - Holdings"], summary="Get portfolio summary")
async def portfolio_summary(portfolio_id: str):
    """Get a high-level portfolio summary.

    Returns an aggregated overview including total value, gain/loss, and
    top holdings.
    """
    try:
        # BUG: passing None for user — will fail if summary tries to access risk_profile
        summary = get_portfolio_summary(portfolio_id, user=None)
        return summary
    except PortfolioNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.put(
    "/portfolio/{portfolio_id}/allocations",
    tags=["Portfolio - Rebalancing"],
    summary="Update target allocations",
)
async def update_allocations(portfolio_id: str, request: AllocationUpdateRequest):
    """Update target allocations for a portfolio.

    Allocations must sum to 100%. Each key is a ticker symbol and the value
    is the target percentage.
    """
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
