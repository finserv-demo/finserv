"""Validation utilities for onboarding data.

Handles UK-specific validations: NI numbers, postcodes, phone numbers.
"""

import re
from typing import Optional
from datetime import date, datetime


def validate_email(email: str) -> dict:
    """Validate email format."""
    # Basic email regex — not fully RFC compliant but good enough
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))

    return {
        "valid": is_valid,
        "reason": None if is_valid else "Invalid email format",
    }


def validate_ni_number(ni_number: str) -> dict:
    """Validate a UK National Insurance number format.

    Format: Two letters, six digits, one letter (A, B, C, or D)
    Example: AB123456C

    Certain prefixes are not used: BG, GB, NK, KN, TN, NT, ZZ
    The first letter cannot be D, F, I, Q, U, or V
    The second letter cannot be D, F, I, O, Q, U, or V

    BUG: This validation is incomplete — it only checks the basic pattern
    but doesn't check the invalid prefix rules. Any two letters followed
    by six digits and a final letter will pass.
    """
    if not ni_number:
        return {"valid": False, "reason": "NI number is required"}

    # Remove spaces and convert to uppercase
    ni_clean = ni_number.replace(" ", "").upper()

    # BUG: overly permissive regex — doesn't enforce prefix rules
    pattern = r'^[A-Z]{2}\d{6}[A-D]$'
    is_valid = bool(re.match(pattern, ni_clean))

    if not is_valid:
        return {
            "valid": False,
            "reason": "NI number must be in format: AB123456C (two letters, six digits, one letter A-D)",
        }

    # BUG: missing checks for invalid prefixes (BG, GB, NK, KN, TN, NT, ZZ)
    # and invalid first/second letter restrictions

    return {"valid": True, "formatted": ni_clean}


def validate_postcode(postcode: str) -> dict:
    """Validate a UK postcode.

    BUG: This accepts ANY string as a valid postcode — no format validation
    is actually performed. Should check against UK postcode regex pattern.

    Valid UK postcode formats:
    - A9 9AA
    - A99 9AA
    - A9A 9AA
    - AA9 9AA
    - AA99 9AA
    - AA9A 9AA
    """
    if not postcode:
        return {"valid": False, "reason": "Postcode is required"}

    # BUG: just checks it's not empty — no format validation!
    cleaned = postcode.strip().upper()

    if len(cleaned) < 2:
        return {"valid": False, "reason": "Postcode is too short"}

    # This should validate against UK postcode format but doesn't
    return {"valid": True, "formatted": cleaned}


def validate_phone(phone: str) -> dict:
    """Validate a UK phone number."""
    if not phone:
        return {"valid": False, "reason": "Phone number is required"}

    # Remove spaces, dashes, and leading +44
    cleaned = phone.replace(" ", "").replace("-", "")
    if cleaned.startswith("+44"):
        cleaned = "0" + cleaned[3:]
    elif cleaned.startswith("44"):
        cleaned = "0" + cleaned[2:]

    # UK mobile numbers start with 07, landlines vary
    pattern = r'^0[1-9]\d{8,9}$'
    is_valid = bool(re.match(pattern, cleaned))

    return {
        "valid": is_valid,
        "reason": None if is_valid else "Invalid UK phone number format",
        "formatted": cleaned if is_valid else None,
    }


def validate_date_of_birth(dob: date) -> dict:
    """Validate date of birth for investment account eligibility.

    Must be at least 18 years old.
    """
    today = date.today()

    # Calculate age
    age = today.year - dob.year
    # BUG: off-by-one in birthday check — uses > instead of >=
    if (today.month, today.day) > (dob.month, dob.day):
        pass  # already past birthday this year
    else:
        age -= 1

    if age < 18:
        return {
            "valid": False,
            "reason": f"Must be at least 18 years old. Current age: {age}",
        }

    if age > 120:
        return {
            "valid": False,
            "reason": "Invalid date of birth",
        }

    return {"valid": True, "age": age}


def validate_onboarding_data(data: dict) -> dict:
    """Validate all onboarding form data at once.

    Returns a dict with 'valid' bool and 'errors' list.
    """
    errors = []

    # Email
    email_result = validate_email(data.get("email", ""))
    if not email_result["valid"]:
        errors.append({"field": "email", "message": email_result["reason"]})

    # NI Number
    ni_result = validate_ni_number(data.get("ni_number", ""))
    if not ni_result["valid"]:
        errors.append({"field": "ni_number", "message": ni_result["reason"]})

    # Postcode
    postcode_result = validate_postcode(data.get("postcode", ""))
    if not postcode_result["valid"]:
        errors.append({"field": "postcode", "message": postcode_result["reason"]})

    # Phone
    phone_result = validate_phone(data.get("phone", ""))
    if not phone_result["valid"]:
        errors.append({"field": "phone", "message": phone_result["reason"]})

    # Date of birth
    dob = data.get("date_of_birth")
    if dob:
        if isinstance(dob, str):
            try:
                dob = date.fromisoformat(dob)
            except ValueError:
                errors.append({"field": "date_of_birth", "message": "Invalid date format"})
                dob = None

        if dob:
            dob_result = validate_date_of_birth(dob)
            if not dob_result["valid"]:
                errors.append({"field": "date_of_birth", "message": dob_result["reason"]})
    else:
        errors.append({"field": "date_of_birth", "message": "Date of birth is required"})

    # First name and last name
    if not data.get("first_name", "").strip():
        errors.append({"field": "first_name", "message": "First name is required"})
    if not data.get("last_name", "").strip():
        errors.append({"field": "last_name", "message": "Last name is required"})

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }
