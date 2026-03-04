"""FastAPI routes for the tax service."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
    user_id: str
    amount: float


class DisposalRequest(BaseModel):
    user_id: str
    symbol: str
    quantity: float
    disposal_price: float
    acquisition_price: float
    disposal_date: Optional[str] = None
    acquisition_date: Optional[str] = None


class BedAndBreakfastCheckRequest(BaseModel):
    user_id: str
    symbol: str
    disposal_date: str
    acquisitions: list[dict]


# --- ISA Routes ---

@router.get("/isa/summary/{user_id}")
async def isa_summary(user_id: str):
    """Get ISA summary for a user."""
    try:
        return get_isa_summary(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/isa/allowance/{user_id}")
async def isa_allowance(user_id: str):
    """Get remaining ISA allowance for the current tax year."""
    remaining = get_remaining_allowance(user_id)
    return {
        "user_id": user_id,
        "tax_year": get_current_tax_year(),
        "remaining_allowance": remaining,
        "currency": "GBP",
    }


@router.post("/isa/contribute")
async def contribute_to_isa(request: ISAContributionRequest):
    """Record an ISA contribution."""
    validation = validate_isa_contribution(request.user_id, request.amount)
    if not validation["valid"]:
        raise HTTPException(status_code=422, detail=validation["reason"])

    result = record_isa_contribution(request.user_id, request.amount)
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["error"])

    return result


# --- CGT Routes ---

@router.get("/cgt/summary/{user_id}")
async def cgt_summary(user_id: str):
    """Get CGT summary for a user."""
    return get_cgt_summary(user_id)


@router.get("/cgt/annual/{user_id}")
async def annual_cgt(user_id: str, tax_year: Optional[str] = None):
    """Calculate annual CGT for a user."""
    if tax_year is None:
        tax_year = get_current_tax_year()
    return calculate_annual_cgt(user_id, tax_year)


@router.post("/cgt/disposal")
async def record_cgt_disposal(request: DisposalRequest):
    """Record a share disposal for CGT purposes."""
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


@router.post("/cgt/bed-and-breakfast-check")
async def check_bed_and_breakfast_rule(request: BedAndBreakfastCheckRequest):
    """Check if a disposal triggers the bed-and-breakfasting rule."""
    disposal_date = date.fromisoformat(request.disposal_date)
    result = check_bed_and_breakfast(
        user_id=request.user_id,
        symbol=request.symbol,
        disposal_date=disposal_date,
        acquisitions=request.acquisitions,
    )
    return result


# --- Tax Loss Harvesting Routes ---

@router.get("/harvesting/opportunities/{user_id}")
async def get_harvesting_opportunities(user_id: str):
    """Get tax-loss harvesting opportunities for a user.

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


@router.get("/tax-year/current")
async def current_tax_year():
    """Get the current UK tax year."""
    return {"tax_year": get_current_tax_year()}
