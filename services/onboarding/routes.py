"""FastAPI routes for the onboarding service."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
    """New onboarding application request."""
    first_name: str = Field(description="Applicant first name", examples=["Jane"])
    last_name: str = Field(description="Applicant last name", examples=["Doe"])
    email: str = Field(description="Applicant email address", examples=["jane.doe@example.com"])
    phone: str = Field(description="UK phone number", examples=["+447700900123"])
    postcode: str = Field(description="UK postcode", examples=["SW1A 1AA"])
    ni_number: str = Field(description="National Insurance number", examples=["QQ 12 34 56 C"])
    date_of_birth: str = Field(description="Date of birth in ISO format", examples=["1990-05-15"])
    user_id: Optional[str] = Field(
        default=None, description="Existing user ID (optional for new users)", examples=["usr_001"]
    )


class KYCStatusUpdate(BaseModel):
    """Request to update a KYC application status."""
    status: str = Field(description="New KYC status", examples=["approved"])
    notes: str = Field(default="", description="Reviewer notes", examples=["Identity documents verified"])


# --- Routes ---

@router.post("/apply", tags=["Onboarding - Applications"], summary="Submit onboarding application")
async def apply(request: OnboardingRequest):
    """Submit a new onboarding application.

    Validates the applicant's details (NI number, postcode, phone) and creates
    a new KYC application.
    """
    result = submit_application(request.model_dump())
    if not result["success"]:
        raise HTTPException(status_code=422, detail=result["errors"])
    return result


@router.get("/application/{app_id}", tags=["Onboarding - Applications"], summary="Get application by ID")
async def get_app(app_id: str):
    """Get an application by ID.

    Returns the full application details including current KYC status.
    """
    app = get_application(app_id)
    if not app:
        raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
    return app


@router.get("/applications/{user_id}", tags=["Onboarding - Applications"], summary="Get user applications")
async def get_user_applications(user_id: str):
    """Get all applications for a user.

    Returns a list of all onboarding applications submitted by the specified user.
    """
    apps = get_applications_for_user(user_id)
    return {"user_id": user_id, "applications": apps, "count": len(apps)}


@router.put("/application/{app_id}/kyc-status", tags=["Onboarding - Verification"], summary="Update KYC status")
async def update_status(app_id: str, request: KYCStatusUpdate):
    """Update the KYC status of an application.

    Transitions the application to a new KYC status (e.g. pending -> in_review -> approved).
    """
    result = update_kyc_status(app_id, request.status, request.notes)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post(
    "/application/{app_id}/verify",
    tags=["Onboarding - Verification"],
    summary="Trigger identity verification",
)
async def verify(app_id: str):
    """Trigger identity verification for an application.

    Initiates the identity verification process for the specified application.
    """
    result = verify_identity(app_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/stats", tags=["Onboarding - Stats"], summary="Get onboarding statistics")
async def stats():
    """Get onboarding statistics.

    Returns aggregate stats on the onboarding pipeline (total applications,
    approval rates, etc.).
    """
    return get_onboarding_stats()


# --- Validation endpoints ---

@router.post("/validate/ni-number", tags=["Onboarding - Validation"], summary="Validate NI number")
async def validate_ni(ni_number: str):
    """Validate a National Insurance number.

    Checks the format of a UK National Insurance number against the standard pattern.
    """
    result = validate_ni_number(ni_number)
    return result


@router.post("/validate/postcode", tags=["Onboarding - Validation"], summary="Validate UK postcode")
async def validate_pc(postcode: str):
    """Validate a UK postcode.

    Checks the format of a UK postcode.

    BUG: This always returns valid for any non-empty string.
    See validators.py validate_postcode().
    """
    result = validate_postcode(postcode)
    return result


@router.post("/validate/phone", tags=["Onboarding - Validation"], summary="Validate UK phone number")
async def validate_ph(phone: str):
    """Validate a UK phone number.

    Checks the format of a UK phone number (landline or mobile).
    """
    result = validate_phone(phone)
    return result
