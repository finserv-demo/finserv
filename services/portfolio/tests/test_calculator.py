"""Tests for portfolio calculator."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.portfolio.calculator import (
    calculate_portfolio_drift,
    calculate_portfolio_value,
    execute_rebalance,
    generate_rebalance_trades,
)
from services.portfolio.db import _holdings, _portfolios, init_db
from services.portfolio.errors import PortfolioNotFoundError


@pytest.fixture(autouse=True)
async def setup_db():
    """Reset and initialize the test database."""
    _portfolios.clear()
    _holdings.clear()
    await init_db()


class TestCalculatePortfolioValue:
    def test_basic_valuation(self):
        result = calculate_portfolio_value("pf_001")
        assert result["portfolio_id"] == "pf_001"
        assert result["total_value"] > 0
        assert result["currency"] == "GBP"
        assert len(result["holdings"]) == 3

    def test_holding_breakdown(self):
        result = calculate_portfolio_value("pf_001")
        vwrl = next(h for h in result["holdings"] if h["symbol"] == "VWRL.L")
        assert vwrl["quantity"] == 150.0
        assert vwrl["current_price"] == 82.30
        assert vwrl["value"] == 150.0 * 82.30

    @pytest.mark.xfail(reason="BUG: gain_loss uses wrong sign convention (issue #5)")
    def test_gain_loss_calculation(self):
        result = calculate_portfolio_value("pf_001")
        vwrl = next(h for h in result["holdings"] if h["symbol"] == "VWRL.L")
        expected_gain = (82.30 - 78.50) * 150.0
        assert vwrl["gain_loss"] == expected_gain

    def test_portfolio_not_found(self):
        with pytest.raises(PortfolioNotFoundError):
            calculate_portfolio_value("nonexistent")


class TestCalculatePortfolioDrift:
    def test_drift_calculation(self):
        result = calculate_portfolio_drift("pf_001")
        assert result["portfolio_id"] == "pf_001"
        assert "holdings_drift" in result
        assert "total_drift_pct" in result

    def test_drift_includes_all_targets(self):
        result = calculate_portfolio_drift("pf_001")
        # CASH target exists but has no holding
        assert "CASH" in result["holdings_drift"]

    def test_empty_portfolio(self):
        result = calculate_portfolio_drift("pf_002")
        # pf_002 has no holdings
        assert result["total_drift_pct"] >= 0


class TestRebalanceTrades:
    def test_generates_trades(self):
        trades = generate_rebalance_trades("pf_001")
        assert isinstance(trades, list)
        for trade in trades:
            assert "symbol" in trade
            assert "trade_type" in trade
            assert "quantity" in trade

    def test_trade_quantities_are_integers(self):
        """This tests the bug — quantities should ideally support fractional shares."""
        trades = generate_rebalance_trades("pf_001")
        for trade in trades:
            assert isinstance(trade["quantity"], int)

    def test_not_found(self):
        with pytest.raises(PortfolioNotFoundError):
            generate_rebalance_trades("nonexistent")


class TestExecuteRebalance:
    def test_execute_updates_holdings(self):
        result = execute_rebalance("pf_001")
        assert result["status"] in ("completed", "no_trades_needed")
