"""Tests for Capital Gains Tax calculations."""

import pytest
import sys
import os
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.tax.cgt import (
    calculate_gain_or_loss,
    check_bed_and_breakfast,
    calculate_annual_cgt,
    record_disposal,
    get_cgt_summary,
    init_cgt_data,
    _cgt_events,
)
from services.tax.constants import CGT_ANNUAL_EXEMPT_AMOUNT


@pytest.fixture(autouse=True)
def setup():
    _cgt_events.clear()
    init_cgt_data()


class TestGainLossCalculation:
    def test_gain(self):
        result = calculate_gain_or_loss(100, 15.0, 10.0)
        assert result["gain_or_loss"] == 500.0
        assert result["is_gain"] is True

    def test_loss(self):
        result = calculate_gain_or_loss(100, 8.0, 10.0)
        assert result["gain_or_loss"] == -200.0
        assert result["is_gain"] is False

    def test_break_even(self):
        result = calculate_gain_or_loss(100, 10.0, 10.0)
        assert result["gain_or_loss"] == 0.0
        assert result["is_gain"] is False


class TestBedAndBreakfast:
    def test_no_matching_acquisitions(self):
        result = check_bed_and_breakfast(
            "user_001", "VOD.L", date(2024, 9, 15), []
        )
        assert result["is_bed_and_breakfast"] is False

    def test_matching_acquisition_within_30_days(self):
        acquisitions = [
            {"symbol": "VOD.L", "date": "2024-09-20", "quantity": 500, "price": 10.0}
        ]
        result = check_bed_and_breakfast(
            "user_001", "VOD.L", date(2024, 9, 15), acquisitions
        )
        assert result["is_bed_and_breakfast"] is True

    def test_acquisition_outside_30_days(self):
        acquisitions = [
            {"symbol": "VOD.L", "date": "2024-11-01", "quantity": 500, "price": 10.0}
        ]
        result = check_bed_and_breakfast(
            "user_001", "VOD.L", date(2024, 9, 15), acquisitions
        )
        assert result["is_bed_and_breakfast"] is False

    def test_different_symbol_not_matched(self):
        acquisitions = [
            {"symbol": "BP.L", "date": "2024-09-20", "quantity": 500, "price": 10.0}
        ]
        result = check_bed_and_breakfast(
            "user_001", "VOD.L", date(2024, 9, 15), acquisitions
        )
        assert result["is_bed_and_breakfast"] is False


class TestAnnualCGT:
    def test_calculate_annual_cgt(self):
        result = calculate_annual_cgt("user_001", "2024/25")
        assert "total_gains" in result
        assert "total_losses" in result
        assert "tax_due" in result
        assert result["annual_exempt_amount"] == CGT_ANNUAL_EXEMPT_AMOUNT


class TestRecordDisposal:
    def test_record_disposal(self):
        result = record_disposal(
            user_id="user_001",
            symbol="TEST.L",
            quantity=100,
            disposal_price=15.0,
            acquisition_price=10.0,
        )
        assert result["calculation"]["gain_or_loss"] == 500.0
