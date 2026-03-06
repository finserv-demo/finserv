"""FastAPI routes for the tax service."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.tax.cgt import (
    calculate_annual_cgt,
    check_bed_and_breakfast,
    get_cgt_summary,
    init_cgt_data,
    record_disposal,
)
from services.tax.isa import (
    get_current_tax_year,
    get_isa_summary,
    get_remaining_allowance,
    init_isa_data,
    record_isa_contribution,
    validate_isa_contribution,
)
from services.tax.tax_loss_harvesting import (
    identify_harvesting_opportunities,
)

router = APIRouter()

# Initialize data on import
init_isa_data()
init_cgt_data()


# --- Request schemas ---

class ISAContributionRequest(BaseModel):
    """Request to record an ISA contribution."""
    user_id: str = Field(description="ID of the contributing user", examples=["usr_001"])
    amount: float = Field(description="Contribution amount in GBP", examples=[5000.0])


class DisposalRequest(BaseModel):
    """Request to record a share disposal for CGT purposes."""
    user_id: str = Field(description="ID of the user disposing shares", examples=["usr_001"])
    symbol: str = Field(description="Ticker symbol of the disposed asset", examples=["VOD.L"])
    quantity: float = Field(description="Number of units disposed", examples=[500.0])
    disposal_price: float = Field(description="Price per unit at disposal in GBP", examples=[5.00])
    acquisition_price: float = Field(description="Original price per unit in GBP", examples=[4.00])
    disposal_date: Optional[str] = Field(
        default=None, description="ISO date of disposal (defaults to today)", examples=["2024-11-15"]
    )
    acquisition_date: Optional[str] = Field(
        default=None, description="ISO date of original acquisition", examples=["2023-03-10"]
    )


class BedAndBreakfastCheckRequest(BaseModel):
    """Request to check whether a disposal triggers the bed-and-breakfasting rule."""
    user_id: str = Field(description="ID of the user", examples=["usr_001"])
    symbol: str = Field(description="Ticker symbol", examples=["VOD.L"])
    disposal_date: str = Field(description="ISO date of the disposal", examples=["2024-11-15"])
    acquisitions: list[dict] = Field(description="List of acquisition records to check against the 30-day window")


# --- ISA Routes ---

@router.get("/isa/summary/{user_id}", tags=["Tax - ISA"], summary="Get ISA summary")
async def isa_summary(user_id: str):
    """Get ISA summary for a user.

    Returns the user's ISA account details including contributions and remaining allowance.
    """
    try:
        return get_isa_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/isa/allowance/{user_id}", tags=["Tax - ISA"], summary="Get remaining ISA allowance")
async def isa_allowance(user_id: str):
    """Get remaining ISA allowance for the current tax year.

    Returns how much of the annual ISA allowance the user has left to contribute.
    """
    remaining = get_remaining_allowance(user_id)
    return {
        "user_id": user_id,
        "tax_year": get_current_tax_year(),
        "remaining_allowance": remaining,
        "currency": "GBP",
    }


@router.post("/isa/contribute", tags=["Tax - ISA"], summary="Record an ISA contribution")
async def contribute_to_isa(request: ISAContributionRequest):
    """Record an ISA contribution.

    Validates that the contribution does not exceed the remaining annual allowance
    before recording it.
    """
    validation = validate_isa_contribution(request.user_id, request.amount)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["reason"])

    result = record_isa_contribution(request.user_id, request.amount)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# --- CGT Routes ---

@router.get("/cgt/summary/{user_id}", tags=["Tax - CGT"], summary="Get CGT summary")
async def cgt_summary(user_id: str):
    """Get Capital Gains Tax summary for a user.

    Returns total gains, losses, and net CGT liability.
    """
    return get_cgt_summary(user_id)


@router.get("/cgt/annual/{user_id}", tags=["Tax - CGT"], summary="Calculate annual CGT")
async def annual_cgt(
    user_id: str,
    tax_year: Optional[str] = Query(default=None, description="Tax year (e.g. '2024/25'). Defaults to current."),
):
    """Calculate annual Capital Gains Tax for a user.

    Computes the CGT liability for the specified (or current) tax year,
    including the annual exempt amount.
    """
    if tax_year is None:
        tax_year = get_current_tax_year()
    return calculate_annual_cgt(user_id, tax_year)


@router.post("/cgt/disposal", tags=["Tax - CGT"], summary="Record a share disposal")
async def record_cgt_disposal(request: DisposalRequest):
    """Record a share disposal for CGT purposes.

    Calculates the gain or loss on the disposal and adds it to the user's
    CGT record for the relevant tax year.
    """
    disposal_date = None
    acquisition_date = None

    if request.disposal_date:
        disposal_date = date.fromisoformat(request.disposal_date)
    if request.acquisition_date:
        acquisition_date = date.fromisoformat(request.acquisition_date)

    result = record_disposal(
        user_id=request.user_id,
        symbol=request.symbol,
        quantity=request.quantity,
        disposal_price=request.disposal_price,
        acquisition_price=request.acquisition_price,
        disposal_date=disposal_date,
        acquisition_date=acquisition_date,
    )
    return result


@router.post("/cgt/bed-and-breakfast-check", tags=["Tax - CGT"], summary="Check bed-and-breakfasting rule")
async def check_bed_and_breakfast_rule(request: BedAndBreakfastCheckRequest):
    """Check if a disposal triggers the bed-and-breakfasting rule.

    The bed-and-breakfasting rule prevents claiming a loss on a disposal
    if the same shares are repurchased within 30 days.
    """
    disposal_date = date.fromisoformat(request.disposal_date)
    result = check_bed_and_breakfast(
        user_id=request.user_id,
        symbol=request.symbol,
        disposal_date=disposal_date,
        acquisitions=request.acquisitions,
    )
    return result


# --- Tax Loss Harvesting Routes ---

@router.get(
    "/harvesting/opportunities/{user_id}",
    tags=["Tax - Harvesting"],
    summary="Get tax-loss harvesting opportunities",
)
async def get_harvesting_opportunities(user_id: str):
    """Get tax-loss harvesting opportunities for a user.

    Identifies holdings currently trading below their cost basis that could
    be sold to realise a loss for CGT offset purposes.

    NOTE: This endpoint needs to fetch holdings from the portfolio service,
    which currently isn't wired up. Using dummy data for now.
    """
    # TODO: fetch real holdings from portfolio service
    dummy_holdings = [
        {
            "symbol": "VOD.L",
            "name": "Vodafone Group",
            "quantity": 500,
            "average_cost": 1.20,
            "current_price": 0.95,
        },
        {
            "symbol": "BP.L",
            "name": "BP plc",
            "quantity": 200,
            "average_cost": 5.50,
            "current_price": 5.10,
        },
        {
            "symbol": "HSBA.L",
            "name": "HSBC Holdings",
            "quantity": 300,
            "average_cost": 6.50,
            "current_price": 7.00,
        },
    ]

    opportunities = identify_harvesting_opportunities(dummy_holdings, [], user_id)
    return {"user_id": user_id, "opportunities": opportunities}


@router.get("/tax-year/current", tags=["Tax - General"], summary="Get current UK tax year")
async def current_tax_year():
    """Get the current UK tax year.

    Returns the tax year string (e.g. '2024/25') for today's date.
    """
    return {"tax_year": get_current_tax_year()}
