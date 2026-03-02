"""Tests for portfolio routes."""

import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi.testclient import TestClient
from services.portfolio.main import app
from services.portfolio.db import init_db, _portfolios, _holdings, _transactions


@pytest.fixture(autouse=True)
async def setup_db():
    _portfolios.clear()
    _holdings.clear()
    _transactions.clear()
    await init_db()


client = TestClient(app)


class TestGetPortfolios:
    def test_get_user_portfolios(self):
        response = client.get("/api/portfolio/portfolios/user_001")
        assert response.status_code == 200
        data = response.json()
        assert "portfolios" in data
        assert len(data["portfolios"]) >= 1

    def test_user_not_found(self):
        response = client.get("/api/portfolio/portfolios/nonexistent")
        assert response.status_code == 404


class TestGetPortfolioDetail:
    def test_get_portfolio(self):
        response = client.get("/api/portfolio/portfolio/pf_001")
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio"]["id"] == "pf_001"
        assert len(data["holdings"]) > 0

    def test_portfolio_not_found(self):
        response = client.get("/api/portfolio/portfolio/nonexistent")
        assert response.status_code == 404


class TestRebalance:
    def test_dry_run(self):
        response = client.post(
            "/api/portfolio/rebalance",
            json={"portfolio_id": "pf_001", "dry_run": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dry_run"

    def test_rebalance_invalid_portfolio(self):
        """BUG: This returns 200 with error in body instead of proper HTTP error."""
        response = client.post(
            "/api/portfolio/rebalance",
            json={"portfolio_id": "nonexistent", "dry_run": False},
        )
        # This should be 404 but is currently 200
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"


class TestTransactions:
    def test_get_transactions(self):
        response = client.get("/api/portfolio/portfolio/pf_001/transactions")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert data["page"] == 1

    def test_get_transactions_with_pagination(self):
        response = client.get("/api/portfolio/portfolio/pf_001/transactions?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) <= 2


class TestPortfolioHistory:
    def test_get_history(self):
        response = client.get("/api/portfolio/portfolio/pf_001/history")
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
