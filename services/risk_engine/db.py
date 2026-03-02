"""In-memory database for risk engine service."""

from datetime import datetime

# In-memory stores
_risk_profiles: dict = {}
_questionnaire_responses: list = []


async def init_db():
    """Initialize with sample risk profile data."""
    _risk_profiles["user_001"] = {
        "user_id": "user_001",
        "score": 6,
        # BUG: uses old field name 'risk_category' instead of 'risk_level'
        # shared/types/models.py RiskProfile uses 'risk_level' but this
        # service still uses the old name
        "risk_category": "moderate",
        "answers": {
            "q1": "c",
            "q2": "c",
            "q3": "c",
            "q4": "b",
            "q5": "c",
            "q6": "c",
            "q7": "c",
        },
        "calculated_at": datetime(2024, 6, 15, 14, 30, 0),
    }

    _risk_profiles["user_002"] = {
        "user_id": "user_002",
        "score": 3,
        "risk_category": "conservative",
        "answers": {
            "q1": "a",
            "q2": "a",
            "q3": "a",
            "q4": "b",
            "q5": "b",
            "q6": "a",
            "q7": "b",
        },
        "calculated_at": datetime(2024, 8, 20, 10, 0, 0),
    }


def get_risk_profile(user_id: str):
    return _risk_profiles.get(user_id)


def save_risk_profile(user_id: str, profile: dict):
    """Save a risk profile.

    BUG: This replaces the entire profile but doesn't invalidate
    any cached risk scores used by the portfolio service.
    """
    _risk_profiles[user_id] = profile
    return profile


def get_all_profiles():
    return list(_risk_profiles.values())


def save_questionnaire_response(response: dict):
    _questionnaire_responses.append(response)
    return response
