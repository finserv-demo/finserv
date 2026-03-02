"""Tests for onboarding validators."""

import pytest
import sys
import os
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.onboarding.validators import (
    validate_email,
    validate_ni_number,
    validate_postcode,
    validate_phone,
    validate_date_of_birth,
    validate_onboarding_data,
)


class TestEmailValidation:
    def test_valid_email(self):
        result = validate_email("test@example.co.uk")
        assert result["valid"] is True

    def test_invalid_email(self):
        result = validate_email("not-an-email")
        assert result["valid"] is False

    def test_empty_email(self):
        result = validate_email("")
        assert result["valid"] is False


class TestNINumberValidation:
    def test_valid_ni_number(self):
        result = validate_ni_number("AB123456C")
        assert result["valid"] is True

    def test_valid_with_spaces(self):
        result = validate_ni_number("AB 12 34 56 C")
        assert result["valid"] is True

    def test_lowercase_is_normalized(self):
        result = validate_ni_number("ab123456c")
        assert result["valid"] is True

    def test_invalid_format(self):
        result = validate_ni_number("1234")
        assert result["valid"] is False

    def test_empty_ni_number(self):
        result = validate_ni_number("")
        assert result["valid"] is False

    def test_invalid_prefix_not_caught(self):
        """Documents bug: invalid prefixes like BG, GB, NK are not rejected."""
        # BG is an invalid prefix in real NI numbers
        result = validate_ni_number("BG123456A")
        # BUG: this should be invalid but passes
        assert result["valid"] is True


class TestPostcodeValidation:
    def test_valid_postcode(self):
        result = validate_postcode("SW1A 1AA")
        assert result["valid"] is True

    def test_any_string_passes(self):
        """Documents bug: any non-empty string passes validation."""
        result = validate_postcode("NOT A POSTCODE")
        # BUG: should be invalid
        assert result["valid"] is True

    def test_empty_postcode(self):
        result = validate_postcode("")
        assert result["valid"] is False


class TestPhoneValidation:
    def test_valid_mobile(self):
        result = validate_phone("07700900123")
        assert result["valid"] is True

    def test_valid_with_country_code(self):
        result = validate_phone("+447700900123")
        assert result["valid"] is True

    def test_invalid_phone(self):
        result = validate_phone("12345")
        assert result["valid"] is False

    def test_empty_phone(self):
        result = validate_phone("")
        assert result["valid"] is False


class TestDateOfBirthValidation:
    def test_adult(self):
        result = validate_date_of_birth(date(1990, 1, 1))
        assert result["valid"] is True
        assert result["age"] >= 18

    def test_underage(self):
        result = validate_date_of_birth(date(2020, 1, 1))
        assert result["valid"] is False

    def test_very_old(self):
        result = validate_date_of_birth(date(1800, 1, 1))
        assert result["valid"] is False


class TestOnboardingDataValidation:
    def test_valid_data(self):
        data = {
            "first_name": "James",
            "last_name": "Smith",
            "email": "james@example.co.uk",
            "phone": "07700900123",
            "postcode": "SW1A 1AA",
            "ni_number": "AB123456C",
            "date_of_birth": "1990-05-15",
        }
        result = validate_onboarding_data(data)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_missing_fields(self):
        result = validate_onboarding_data({})
        assert result["valid"] is False
        assert len(result["errors"]) > 0
