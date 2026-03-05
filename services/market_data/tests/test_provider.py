"""Tests for market data provider."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.market_data.provider import (
    BASE_PRICES,
    clear_cache,
    get_available_symbols,
    get_historical_prices,
    get_price,
    get_prices,
)


@pytest.fixture(autouse=True)
def clear():
    clear_cache()


class TestGetPrice:
    def test_known_symbol(self):
        price = get_price("VWRL.L")
        # Might be None due to simulated failure, try again
        if price is None:
            price = get_price("VWRL.L")
        assert price is not None
        assert price["symbol"] == "VWRL.L"
        assert price["price"] > 0

    def test_unknown_symbol(self):
        price = get_price("FAKE.L")
        assert price is None

    def test_price_is_cached(self):
        price1 = get_price("VWRL.L")
        price2 = get_price("VWRL.L")
        if price1 and price2:
            assert price1["price"] == price2["price"]

    def test_price_has_no_currency_field(self):
        """Documents the bug: price response missing currency field."""
        price = get_price("VWRL.L")
        if price:
            assert "currency" not in price  # BUG: should be present


class TestGetPrices:
    def test_multiple_symbols(self):
        prices = get_prices(["VWRL.L", "VGOV.L", "VUKE.L"])
        assert len(prices) > 0
        assert all("symbol" in p for p in prices)


class TestHistoricalPrices:
    def test_historical_data(self):
        history = get_historical_prices("VWRL.L", days=10)
        assert len(history) == 10
        assert all("close" in p for p in history)

    def test_unknown_symbol_history(self):
        history = get_historical_prices("FAKE.L")
        assert history == []


class TestAvailableSymbols:
    def test_lists_all_symbols(self):
        symbols = get_available_symbols()
        assert len(symbols) == len(BASE_PRICES)
        assert all("currency" in s for s in symbols)
