"""Market data provider — fetches prices from external APIs.

In production this would connect to a real market data provider
(e.g. Bloomberg, Refinitiv, or a free API like Alpha Vantage).
For the demo, we use simulated data with realistic price movements.
"""

import random
import time
from datetime import datetime, timedelta
from typing import Optional

# Simulated market data for LSE-listed securities
_price_cache: dict = {}
_cache_timestamps: dict = {}

# Cache TTL in seconds — should be configurable
CACHE_TTL_SECONDS = 300  # 5 minutes — too long for real trading, too short for demo

# Base prices for simulation
BASE_PRICES = {
    "VWRL.L": 82.30,
    "VGOV.L": 20.85,
    "VUKE.L": 33.15,
    "VMID.L": 40.50,
    "VOD.L": 0.72,
    "BP.L": 5.10,
    "HSBA.L": 7.15,
    "SHEL.L": 27.40,
    "AZN.L": 118.50,
    "GSK.L": 15.80,
    "ULVR.L": 42.60,
    "RIO.L": 55.20,
    "LLOY.L": 0.55,
    "BARC.L": 2.15,
    "GLEN.L": 4.80,
}


def _simulate_price_movement(base_price: float) -> float:
    """Simulate a realistic intraday price movement."""
    # Random walk with slight upward bias
    change_pct = random.gauss(0.001, 0.02)  # mean 0.1%, std dev 2%
    new_price = base_price * (1 + change_pct)
    return round(new_price, 2)


def _simulate_volume() -> int:
    """Simulate trading volume."""
    return random.randint(100000, 5000000)


def get_price(symbol: str) -> Optional[dict]:
    """Get the current price for a symbol.

    Uses a simple in-memory cache. If cached price is fresh enough, returns it.
    Otherwise, fetches a new price (simulated).

    BUG: No retry logic for failed fetches. If the simulated provider
    "fails" (random chance), returns None silently instead of retrying.
    In production, this would mean stale prices are served without
    any indication to the consumer.
    """
    now = time.time()

    # Check cache
    if symbol in _price_cache:
        cache_age = now - _cache_timestamps.get(symbol, 0)
        if cache_age < CACHE_TTL_SECONDS:
            return _price_cache[symbol]

    # Simulate occasional API failure (5% chance)
    # BUG: silently returns stale cached data on failure instead of raising
    if random.random() < 0.05:
        if symbol in _price_cache:
            return _price_cache[symbol]  # return stale data silently
        return None

    # Simulate fetching new price
    base = BASE_PRICES.get(symbol)
    if base is None:
        return None

    price = _simulate_price_movement(base)
    change_pct = round((price - base) / base * 100, 2)

    # BUG: response missing 'currency' field — consumers assume GBP
    # but it's not explicit in the response schema
    price_data = {
        "symbol": symbol,
        "price": price,
        "change_pct": change_pct,
        "volume": _simulate_volume(),
        "timestamp": datetime.utcnow().isoformat(),
        # missing: "currency": "GBP"
    }

    # Update cache
    _price_cache[symbol] = price_data
    _cache_timestamps[symbol] = now

    return price_data


def get_prices(symbols: list[str]) -> list[dict]:
    """Get prices for multiple symbols."""
    results = []
    for symbol in symbols:
        price = get_price(symbol)
        if price:
            results.append(price)
    return results


def get_historical_prices(
    symbol: str,
    days: int = 30,
    interval: str = "daily",
) -> list[dict]:
    """Get historical price data for a symbol.

    Generates simulated historical data based on the base price
    with random walk.
    """
    base = BASE_PRICES.get(symbol)
    if base is None:
        return []

    prices = []
    current_price = base * 0.95  # start a bit lower than current

    for i in range(days):
        date = datetime.utcnow() - timedelta(days=days - i)
        current_price = _simulate_price_movement(current_price)

        prices.append({
            "symbol": symbol,
            "date": date.strftime("%Y-%m-%d"),
            "open": round(current_price * random.uniform(0.99, 1.01), 2),
            "high": round(current_price * random.uniform(1.0, 1.03), 2),
            "low": round(current_price * random.uniform(0.97, 1.0), 2),
            "close": current_price,
            "volume": _simulate_volume(),
        })

    return prices


def get_available_symbols() -> list[dict]:
    """Get all available symbols with their base information."""
    symbols = []
    for symbol, base_price in BASE_PRICES.items():
        symbols.append({
            "symbol": symbol,
            "base_price": base_price,
            "exchange": "LSE",
            "currency": "GBP",
        })
    return symbols


def clear_cache():
    """Clear the price cache."""
    _price_cache.clear()
    _cache_timestamps.clear()
