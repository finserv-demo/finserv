"""Capital Gains Tax (CGT) calculations for UK tax compliance.

Handles disposal calculations, annual exempt amount tracking,
and bed-and-breakfasting rule enforcement.
"""

from datetime import datetime, date, timedelta
from typing import Optional

from services.tax.constants import (
    CGT_ANNUAL_EXEMPT_AMOUNT,
    CGT_BASIC_RATE,
    CGT_HIGHER_RATE,
    BED_AND_BREAKFAST_DAYS,
)


# In-memory store for CGT events
_cgt_events: list = []
_disposals: list = []


def init_cgt_data():
    """Initialize sample CGT data."""
    _cgt_events.extend([
        {
            "id": "cgt_001",
            "user_id": "user_001",
            "symbol": "VOD.L",
            "disposal_date": date(2024, 9, 15),
            "acquisition_date": date(2024, 1, 10),
            "quantity": 500,
            "proceeds": 5250.00,
            "cost_basis": 4800.00,
            "gain_or_loss": 450.00,
        },
        {
            "id": "cgt_002",
            "user_id": "user_001",
            "symbol": "BP.L",
            "disposal_date": date(2024, 10, 20),
            "acquisition_date": date(2023, 6, 5),
            "quantity": 200,
            "proceeds": 1020.00,
            "cost_basis": 1100.00,
            "gain_or_loss": -80.00,
        },
        {
            "id": "cgt_003",
            "user_id": "user_001",
            "symbol": "HSBA.L",
            "disposal_date": date(2024, 11, 5),
            "acquisition_date": date(2024, 3, 20),
            "quantity": 300,
            "proceeds": 2100.00,
            "cost_basis": 1950.00,
            "gain_or_loss": 150.00,
        },
    ])


def calculate_gain_or_loss(
    quantity: float,
    disposal_price: float,
    acquisition_price: float,
) -> dict:
    """Calculate the gain or loss on a disposal."""
    proceeds = quantity * disposal_price
    cost_basis = quantity * acquisition_price

    gain_or_loss = proceeds - cost_basis

    return {
        "proceeds": round(proceeds, 2),
        "cost_basis": round(cost_basis, 2),
        "gain_or_loss": round(gain_or_loss, 2),
        "is_gain": gain_or_loss > 0,
    }


def check_bed_and_breakfast(
    user_id: str,
    symbol: str,
    disposal_date: date,
    acquisitions: list[dict],
) -> dict:
    """Check if a disposal is affected by the bed-and-breakfasting rule.

    The UK 30-day rule: if you sell shares and repurchase the same shares
    within 30 days, the disposal must be matched against the repurchase
    for CGT purposes (not the original acquisition cost).

    BUG: This implementation only checks forward 30 days from disposal,
    but the actual rule also requires checking acquisitions made BEFORE
    the disposal in certain matching order (same-day, then 30-day, then
    section 104 pool). This simplified version misses same-day matching.
    """
    bed_and_breakfast_window = disposal_date + timedelta(days=BED_AND_BREAKFAST_DAYS)

    matching_acquisitions = []
    for acq in acquisitions:
        acq_date = acq.get("date")
        if isinstance(acq_date, str):
            acq_date = date.fromisoformat(acq_date)

        if acq.get("symbol") == symbol and disposal_date < acq_date <= bed_and_breakfast_window:
            matching_acquisitions.append(acq)

    if matching_acquisitions:
        return {
            "is_bed_and_breakfast": True,
            "matching_acquisitions": matching_acquisitions,
            "window_end": bed_and_breakfast_window.isoformat(),
            "message": f"Disposal of {symbol} on {disposal_date} has matching acquisitions within 30 days",
        }

    return {
        "is_bed_and_breakfast": False,
        "matching_acquisitions": [],
        "window_end": bed_and_breakfast_window.isoformat(),
    }


def calculate_annual_cgt(user_id: str, tax_year: str) -> dict:
    """Calculate total CGT liability for a user in a given tax year.

    BUG: Doesn't properly separate gains by asset type (residential property
    vs other assets have different rates). Currently applies the same rate
    to everything.
    """
    from services.tax.isa import get_tax_year_start, get_tax_year_end

    year_start = get_tax_year_start(tax_year)
    year_end = get_tax_year_end(tax_year)

    # Get all CGT events for this user in this tax year
    events = [
        e for e in _cgt_events
        if e["user_id"] == user_id
        and year_start <= e["disposal_date"] <= year_end  # BUG: uses <= for end date, off-by-one from tax year end bug
    ]

    total_gains = sum(e["gain_or_loss"] for e in events if e["gain_or_loss"] > 0)
    total_losses = sum(e["gain_or_loss"] for e in events if e["gain_or_loss"] < 0)
    net_gains = total_gains + total_losses  # losses are negative

    # Apply annual exempt amount
    taxable_gains = max(0, net_gains - CGT_ANNUAL_EXEMPT_AMOUNT)

    # Calculate tax at basic rate (simplified — should check user's income tax band)
    # BUG: always uses basic rate, never checks if user is higher rate taxpayer
    tax_due = taxable_gains * (CGT_BASIC_RATE / 100)

    return {
        "user_id": user_id,
        "tax_year": tax_year,
        "total_gains": round(total_gains, 2),
        "total_losses": round(abs(total_losses), 2),
        "net_gains": round(net_gains, 2),
        "annual_exempt_amount": CGT_ANNUAL_EXEMPT_AMOUNT,
        "taxable_gains": round(taxable_gains, 2),
        "tax_due": round(tax_due, 2),
        "events_count": len(events),
        "events": events,
    }


def record_disposal(
    user_id: str,
    symbol: str,
    quantity: float,
    disposal_price: float,
    acquisition_price: float,
    disposal_date: Optional[date] = None,
    acquisition_date: Optional[date] = None,
) -> dict:
    """Record a share disposal for CGT purposes."""
    if disposal_date is None:
        disposal_date = date.today()
    if acquisition_date is None:
        acquisition_date = date.today() - timedelta(days=365)

    calc = calculate_gain_or_loss(quantity, disposal_price, acquisition_price)

    event = {
        "id": f"cgt_{len(_cgt_events) + 1:03d}",
        "user_id": user_id,
        "symbol": symbol,
        "disposal_date": disposal_date,
        "acquisition_date": acquisition_date,
        "quantity": quantity,
        "proceeds": calc["proceeds"],
        "cost_basis": calc["cost_basis"],
        "gain_or_loss": calc["gain_or_loss"],
    }
    _cgt_events.append(event)

    return {
        "event": event,
        "calculation": calc,
    }


def get_cgt_summary(user_id: str) -> dict:
    """Get a summary of CGT events for a user."""
    user_events = [e for e in _cgt_events if e["user_id"] == user_id]

    total_gains = sum(e["gain_or_loss"] for e in user_events if e["gain_or_loss"] > 0)
    total_losses = sum(abs(e["gain_or_loss"]) for e in user_events if e["gain_or_loss"] < 0)

    return {
        "user_id": user_id,
        "total_events": len(user_events),
        "total_gains": round(total_gains, 2),
        "total_losses": round(total_losses, 2),
        "net_position": round(total_gains - total_losses, 2),
        "annual_exempt_amount": CGT_ANNUAL_EXEMPT_AMOUNT,
    }
