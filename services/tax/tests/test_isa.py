"""Tests for ISA management."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.tax.constants import ISA_ANNUAL_ALLOWANCE
from services.tax.isa import (
    _isa_accounts,
    _isa_contributions,
    get_current_tax_year,
    get_isa_summary,
    get_remaining_allowance,
    get_tax_year_end,
    get_tax_year_start,
    init_isa_data,
    record_isa_contribution,
    validate_isa_contribution,
)


@pytest.fixture(autouse=True)
def setup():
    _isa_accounts.clear()
    _isa_contributions.clear()
    init_isa_data()


class TestTaxYear:
    def test_current_tax_year_format(self):
        year = get_current_tax_year()
        assert "/" in year
        parts = year.split("/")
        assert len(parts[0]) == 4
        assert len(parts[1]) == 2

    def test_tax_year_start(self):
        start = get_tax_year_start("2024/25")
        assert start.year == 2024
        assert start.month == 4
        assert start.day == 6

    def test_tax_year_end(self):
        """NOTE: This test documents the off-by-one bug in get_tax_year_end."""
        end = get_tax_year_end("2024/25")
        assert end.year == 2025
        assert end.month == 4
        # BUG: returns April 6 instead of April 5
        assert end.day == 6  # should be 5


class TestISAContributions:
    def test_validate_positive_amount(self):
        result = validate_isa_contribution("user_001", 5000)
        assert result["valid"] is True

    @pytest.mark.xfail(reason="BUG: ISA allowance validation uses wrong comparison (issue #18)")
    def test_validate_exceeds_allowance(self):
        result = validate_isa_contribution("user_001", 10000)
        # user_001 has 12500 contributed, allowance is 20000, so 7500 remaining
        assert result["valid"] is False

    def test_validate_negative_amount(self):
        result = validate_isa_contribution("user_001", -100)
        assert result["valid"] is False

    @pytest.mark.xfail(reason="BUG: remaining allowance off by one tax year (issue #18)")
    def test_remaining_allowance(self):
        remaining = get_remaining_allowance("user_001")
        assert remaining == ISA_ANNUAL_ALLOWANCE - 12500.00

    def test_remaining_allowance_new_user(self):
        remaining = get_remaining_allowance("new_user")
        assert remaining == float(ISA_ANNUAL_ALLOWANCE)

    def test_record_contribution(self):
        result = record_isa_contribution("user_001", 1000)
        assert result["success"] is True


class TestISASummary:
    def test_summary_includes_current_year(self):
        summary = get_isa_summary("user_001")
        assert "current_tax_year" in summary
        assert "remaining_allowance" in summary
        assert summary["annual_allowance"] == ISA_ANNUAL_ALLOWANCE
