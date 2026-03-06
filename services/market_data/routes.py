"""FastAPI routes for the market data service."""


from fastapi import APIRouter, HTTPException, Query

from services.market_data.provider import (
    get_available_symbols,
    get_historical_prices,
    get_price,
    get_prices,
)

router = APIRouter()


@router.get("/prices", tags=["Market Data - Prices"], summary="Get current prices for multiple symbols")
async def get_market_prices(
    symbols: str = Query(..., description="Comma-separated list of symbols", examples=["VWRL.L,VGOV.L,BP.L"]),
):
    """Get current prices for one or more symbols.

    Pass a comma-separated list of LSE ticker symbols to retrieve the latest
    price, daily change percentage, and volume for each.

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


@router.get("/prices/{symbol}", tags=["Market Data - Prices"], summary="Get price for a single symbol")
async def get_symbol_price(symbol: str):
    """Get the current price for a single symbol.

    Returns the latest quote including price, daily change, and volume.
    """
    price = get_price(symbol)
    if not price:
        raise HTTPException(status_code=404, detail=f"Price not found for symbol {symbol}")
    return price


@router.get("/prices/{symbol}/history", tags=["Market Data - Prices"], summary="Get historical price data")
async def get_price_history(
    symbol: str,
    days: int = Query(default=30, ge=1, le=365, description="Number of days of history to return"),
    interval: str = Query(default="daily", description="Data interval (e.g. 'daily')"),
):
    """Get historical OHLCV price data for a symbol.

    Returns up to 365 days of historical open/high/low/close/volume data
    at the specified interval.
    """
    history = get_historical_prices(symbol, days=days, interval=interval)
    if not history:
        raise HTTPException(status_code=404, detail=f"No historical data for symbol {symbol}")

    return {
        "symbol": symbol,
        "interval": interval,
        "data": history,
        "count": len(history),
    }


@router.get("/symbols", tags=["Market Data - Symbols"], summary="List available symbols")
async def list_symbols():
    """List all available symbols.

    Returns the full list of tradeable symbols supported by the market data provider.
    """
    symbols = get_available_symbols()
    return {"symbols": symbols, "count": len(symbols)}
