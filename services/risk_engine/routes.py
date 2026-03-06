"""FastAPI routes for the risk engine service."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.risk_engine.db import (
    get_risk_profile,
    save_questionnaire_response,
    save_risk_profile,
)
from services.risk_engine.questionnaire import (
    calculate_risk_score,
    get_questionnaire,
    get_recommended_allocation,
)

router = APIRouter()


class QuestionnaireSubmission(BaseModel):
    """Submission of risk questionnaire answers."""
    user_id: str = Field(description="ID of the user submitting the questionnaire", examples=["usr_001"])
    answers: dict = Field(
        description="Questionnaire answers keyed by question ID",
        examples=[{"q1": "b", "q2": "c", "q3": "a"}],
    )


# --- Routes ---

@router.get("/questionnaire", tags=["Risk - Questionnaire"], summary="Get risk questionnaire")
async def get_risk_questionnaire():
    """Get the risk assessment questionnaire.

    Returns the full list of questions and answer options for the risk profiling
    questionnaire.
    """
    return get_questionnaire()


@router.post("/questionnaire/submit", tags=["Risk - Questionnaire"], summary="Submit questionnaire answers")
async def submit_questionnaire(submission: QuestionnaireSubmission):
    """Submit questionnaire answers and calculate risk score.

    Scores the answers, saves the resulting risk profile, and returns the
    profile along with a recommended portfolio allocation.

    BUG: After calculating a new risk score, this saves the profile
    but does NOT notify the portfolio service to update the user's
    portfolio allocation.
    """
    result = calculate_risk_score(submission.answers)

    profile = {
        "user_id": submission.user_id,
        "score": result["score"],
        "risk_category": result["risk_level"],  # BUG: uses 'risk_category' not 'risk_level'
        "answers": submission.answers,
        "calculated_at": datetime.utcnow(),
    }
    save_risk_profile(submission.user_id, profile)

    save_questionnaire_response({
        "user_id": submission.user_id,
        "answers": submission.answers,
        "score": result["score"],
        "submitted_at": datetime.utcnow().isoformat(),
    })

    allocation = get_recommended_allocation(result["risk_level"])

    return {
        "profile": {
            "user_id": submission.user_id,
            "score": result["score"],
            "risk_level": result["risk_level"],
            "calculated_at": datetime.utcnow().isoformat(),
        },
        "breakdown": result["breakdown"],
        "recommended_allocation": allocation,
    }


@router.get("/profile/{user_id}", tags=["Risk - Profile"], summary="Get user risk profile")
async def get_user_risk_profile(user_id: str):
    """Get a user's current risk profile.

    Returns the user's risk score, risk level, and when the profile was calculated.
    """
    profile = get_risk_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No risk profile found for user {user_id}")

    return {
        "user_id": profile["user_id"],
        "score": profile["score"],
        "risk_level": profile.get("risk_category", "moderate"),
        "calculated_at": (
            profile["calculated_at"].isoformat()
            if isinstance(profile["calculated_at"], datetime)
            else profile["calculated_at"]
        ),
    }


@router.get("/profile/{user_id}/allocation", tags=["Risk - Profile"], summary="Get recommended allocation")
async def get_user_allocation(user_id: str):
    """Get the recommended allocation for a user based on their risk profile.

    Returns the target asset class percentages recommended for the user's
    risk level (e.g. equities, bonds, cash).
    """
    profile = get_risk_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"No risk profile found for user {user_id}")

    risk_level = profile.get("risk_category", "moderate")
    allocation = get_recommended_allocation(risk_level)

    return {
        "user_id": user_id,
        "risk_level": risk_level,
        "allocation": allocation["allocation"],
    }
