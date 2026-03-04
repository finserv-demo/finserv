"""FastAPI routes for the onboarding service."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.onboarding.kyc import (
    get_application,
    get_applications_for_user,
    get_onboarding_stats,
    init_onboarding_data,
    submit_application,
    update_kyc_status,
    verify_identity,
)
from services.onboarding.validators import (
    validate_ni_number,
    validate_phone,
    validate_postcode,
)

router = APIRouter()

# Initialize sample data
init_onboarding_data()


# --- Request schemas ---

class OnboardingRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    postcode: str
    ni_number: str
    date_of_birth: str
    user_id: Optional[str] = None


class KYCStatusUpdate(BaseModel):
    status: str
    notes: str = ""


# --- Routes ---

@router.post("/apply")
async def apply(request: OnboardingRequest):
    """Submit a new onboarding application."""
    result = submit_application(request.model_dump())
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    return result


@router.get("/application/{app_id}")
async def get_app(app_id: str):
    """Get an application by ID."""
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
    return app


@router.get("/applications/{user_id}")
async def get_user_applications(user_id: str):
    """Get all applications for a user."""
    apps = get_applications_for_user(user_id)
    return {"user_id": user_id, "applications": apps, "count": len(apps)}


@router.put("/application/{app_id}/kyc-status")
async def update_status(app_id: str, request: KYCStatusUpdate):
    """Update the KYC status of an application."""
    result = update_kyc_status(app_id, request.status, request.notes)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/application/{app_id}/verify")
async def verify(app_id: str):
    """Trigger identity verification for an application."""
    result = verify_identity(app_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/stats")
async def stats():
    """Get onboarding statistics."""
    return get_onboarding_stats()


# --- Validation endpoints ---

@router.post("/validate/ni-number")
async def validate_ni(ni_number: str):
    """Validate a National Insurance number."""
    result = validate_ni_number(ni_number)
    return result


@router.post("/validate/postcode")
async def validate_pc(postcode: str):
    """Validate a UK postcode.

    BUG: This always returns valid for any non-empty string.
    See validators.py validate_postcode().
    """
    result = validate_postcode(postcode)
    return result


@router.post("/validate/phone")
async def validate_ph(phone: str):
    """Validate a UK phone number."""
    result = validate_phone(phone)
    return result
