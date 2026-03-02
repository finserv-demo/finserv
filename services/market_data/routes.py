"""FastAPI routes for the market data service."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from services.market_data.provider import (
    get_price,
    get_prices,
    get_historical_prices,
    get_available_symbols,
)

router = APIRouter()


@router.get("/prices")
async def get_market_prices(symbols: str = Query(..., description="Comma-separated list of symbols")):
    """Get current prices for one or more symbols.

    BUG: Response schema is missing the 'currency' field.
    See schemas.py PriceResponse.
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    prices = get_prices(symbol_list)

    if not prices:
        raise HTTPException(status_code=404, detail="No prices found for the requested symbols")

    return {
        "prices": prices,
        "count": len(prices),
    }


@router.get("/prices/{symbol}")
async def get_symbol_price(symbol: str):
    """Get the current price for a single symbol."""
    price = get_price(symbol)
    if not price:
        raise HTTPException(status_code=404, detail=f"Price not found for symbol {symbol}")
    return price


@router.get("/prices/{symbol}/history")
async def get_price_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365),
    interval: str = Query(default="daily"),
):
    """Get historical price data for a symbol."""
    history = get_historical_prices(symbol, days=days, interval=interval)
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical data for symbol {symbol}")

    return {
        "symbol": symbol,
        "interval": interval,
        "data": history,
        "count": len(history),
    }


@router.get("/symbols")
async def list_symbols():
    """List all available symbols."""
    symbols = get_available_symbols()
    return {"symbols": symbols, "count": len(symbols)}
