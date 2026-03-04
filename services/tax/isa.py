"""ISA (Individual Savings Account) management.

Handles ISA contribution tracking, allowance checks, and tax year rollovers.
"""

from datetime import date, datetime
from typing import Optional

from services.tax.constants import ISA_ANNUAL_ALLOWANCE, TAX_YEAR_START_DAY, TAX_YEAR_START_MONTH

# In-memory store for ISA accounts
_isa_accounts: dict = {}
_isa_contributions: list = []


def init_isa_data():
    """Initialize sample ISA data."""
    _isa_accounts["isa_001"] = {
        "id": "isa_001",
        "user_id": "user_001",
        "tax_year": "2024/25",
        "contributions_ytd": 12500.00,
        "annual_allowance": ISA_ANNUAL_ALLOWANCE,
        "opened_at": datetime(2024, 5, 1),
    }
    _isa_accounts["isa_002"] = {
        "id": "isa_002",
        "user_id": "user_001",
        "tax_year": "2023/24",
        "contributions_ytd": 18000.00,
        "annual_allowance": ISA_ANNUAL_ALLOWANCE,
        "opened_at": datetime(2023, 6, 15),
    }


def get_current_tax_year() -> str:
    """Get the current UK tax year string (e.g. '2024/25').

    UK tax year runs April 6 to April 5.
    """
    today = date.today()
    if today.month > TAX_YEAR_START_MONTH or (
        today.month == TAX_YEAR_START_MONTH and today.day >= TAX_YEAR_START_DAY
    ):
        start_year = today.year
    else:
        start_year = today.year - 1

    end_year = start_year + 1
    return f"{start_year}/{str(end_year)[-2:]}"


def get_tax_year_start(tax_year: str) -> date:
    """Get the start date for a tax year string like '2024/25'."""
    start_year = int(tax_year.split("/")[0])
    return date(start_year, TAX_YEAR_START_MONTH, TAX_YEAR_START_DAY)


def get_tax_year_end(tax_year: str) -> date:
    """Get the end date for a tax year string like '2024/25'.

    BUG: Off-by-one error — tax year ends April 5, not April 6.
    This returns April 6 which is actually the START of the next tax year.
    """
    start_year = int(tax_year.split("/")[0])
    # BUG: should be April 5, not April 6
    return date(start_year + 1, TAX_YEAR_START_MONTH, TAX_YEAR_START_DAY)


def get_isa_account(user_id: str, tax_year: Optional[str] = None) -> Optional[dict]:
    """Get a user's ISA account for a given tax year."""
    if tax_year is None:
        tax_year = get_current_tax_year()

    for account in _isa_accounts.values():
        if account["user_id"] == user_id and account["tax_year"] == tax_year:
            return account
    return None


def get_remaining_allowance(user_id: str, tax_year: Optional[str] = None) -> float:
    """Get the remaining ISA allowance for a user in the current tax year."""
    account = get_isa_account(user_id, tax_year)
    if not account:
        return float(ISA_ANNUAL_ALLOWANCE)

    remaining = account["annual_allowance"] - account["contributions_ytd"]
    return max(0, remaining)


def validate_isa_contribution(user_id: str, amount: float) -> dict:
    """Validate whether an ISA contribution is allowed.

    Returns a dict with 'valid' bool and 'reason' if invalid.
    """
    if amount <= 0:
        return {"valid": False, "reason": "Contribution amount must be positive"}

    remaining = get_remaining_allowance(user_id)

    if amount > remaining:
        return {
            "valid": False,
            "reason": f"Contribution of £{amount:.2f} exceeds remaining allowance of £{remaining:.2f}",
        }

    return {"valid": True, "remaining_after": remaining - amount}


def record_isa_contribution(user_id: str, amount: float) -> dict:
    """Record an ISA contribution for the current tax year.

    BUG: Does not check if we've rolled over to a new tax year.
    If user makes a contribution after April 6, it still counts against
    the OLD tax year's allowance instead of the new one.
    """
    tax_year = get_current_tax_year()
    account = get_isa_account(user_id, tax_year)

    if not account:
        # Create new ISA account for this tax year
        account_id = f"isa_{len(_isa_accounts) + 1:03d}"
        account = {
            "id": account_id,
            "user_id": user_id,
            "tax_year": tax_year,
            "contributions_ytd": 0.0,
            "annual_allowance": ISA_ANNUAL_ALLOWANCE,
            "opened_at": datetime.now(),
        }
        _isa_accounts[account_id] = account

    # Validate contribution
    validation = validate_isa_contribution(user_id, amount)
    if not validation["valid"]:
        return {"success": False, "error": validation["reason"]}

    # BUG: doesn't reset contributions_ytd on new tax year rollover
    # If the user's last contribution was in the previous tax year,
    # contributions_ytd should have been reset to 0 first
    account["contributions_ytd"] += amount

    contribution = {
        "user_id": user_id,
        "amount": amount,
        "tax_year": tax_year,
        "timestamp": datetime.now(),
        "remaining_allowance": account["annual_allowance"] - account["contributions_ytd"],
    }
    _isa_contributions.append(contribution)

    return {
        "success": True,
        "contribution": contribution,
    }


def get_isa_summary(user_id: str) -> dict:
    """Get ISA summary for a user across all tax years."""
    accounts = [a for a in _isa_accounts.values() if a["user_id"] == user_id]

    current_year = get_current_tax_year()
    current_account = next((a for a in accounts if a["tax_year"] == current_year), None)

    return {
        "user_id": user_id,
        "current_tax_year": current_year,
        "contributions_ytd": current_account["contributions_ytd"] if current_account else 0.0,
        "remaining_allowance": get_remaining_allowance(user_id),
        "annual_allowance": ISA_ANNUAL_ALLOWANCE,
        "total_accounts": len(accounts),
        "accounts": accounts,
    }
