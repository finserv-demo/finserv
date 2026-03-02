"""KYC (Know Your Customer) processing for onboarding.

Handles identity verification, document checks, and compliance status.
In production, this would integrate with a KYC provider like Onfido or Jumio.
"""

import uuid
from datetime import datetime
from typing import Optional

from services.onboarding.validators import validate_onboarding_data


# In-memory store for applications
_applications: dict = {}


def init_onboarding_data():
    """Initialize sample onboarding applications."""
    _applications["app_001"] = {
        "id": "app_001",
        "user_id": "user_001",
        "first_name": "James",
        "last_name": "Smith",
        "email": "james.smith@example.co.uk",
        "phone": "07700900123",
        "postcode": "SW1A 1AA",
        "ni_number": "AB123456C",
        "date_of_birth": "1990-05-15",
        "kyc_status": "approved",
        "identity_verified": True,
        "submitted_at": datetime(2024, 1, 10, 14, 30, 0),
        "reviewed_at": datetime(2024, 1, 10, 15, 0, 0),
    }

    _applications["app_002"] = {
        "id": "app_002",
        "user_id": "user_002",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.j@example.co.uk",
        "phone": "07700900456",
        "postcode": "EC2R 8AH",
        "ni_number": "CD654321B",
        "date_of_birth": "1985-11-22",
        "kyc_status": "approved",
        "identity_verified": True,
        "submitted_at": datetime(2024, 2, 5, 10, 15, 0),
        "reviewed_at": datetime(2024, 2, 5, 11, 0, 0),
    }

    _applications["app_003"] = {
        "id": "app_003",
        "user_id": "user_003",
        "first_name": "Ahmed",
        "last_name": "Khan",
        "email": "ahmed.khan@example.co.uk",
        "phone": "07700900789",
        "postcode": "M1 1AA",
        "ni_number": "EF789012A",
        "date_of_birth": "1995-03-08",
        "kyc_status": "pending",
        "identity_verified": False,
        "submitted_at": datetime(2024, 11, 20, 16, 45, 0),
        "reviewed_at": None,
    }


def submit_application(data: dict) -> dict:
    """Submit a new onboarding application.

    Validates all input data and creates a pending application.
    """
    # Validate all fields
    validation = validate_onboarding_data(data)
    if not validation["valid"]:
        return {
            "success": False,
            "errors": validation["errors"],
        }

    app_id = f"app_{uuid.uuid4().hex[:8]}"
    application = {
        "id": app_id,
        "user_id": data.get("user_id", f"user_{uuid.uuid4().hex[:8]}"),
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "phone": data["phone"],
        "postcode": data["postcode"],
        "ni_number": data["ni_number"],
        "date_of_birth": data["date_of_birth"],
        "kyc_status": "pending",
        "identity_verified": False,
        "submitted_at": datetime.utcnow(),
        "reviewed_at": None,
    }

    _applications[app_id] = application

    return {
        "success": True,
        "application_id": app_id,
        "status": "pending",
        "message": "Application submitted successfully. KYC review will be completed within 24 hours.",
    }


def get_application(app_id: str) -> Optional[dict]:
    """Get an application by ID."""
    return _applications.get(app_id)


def get_applications_for_user(user_id: str) -> list[dict]:
    """Get all applications for a user."""
    return [a for a in _applications.values() if a["user_id"] == user_id]


def update_kyc_status(app_id: str, status: str, notes: str = "") -> dict:
    """Update the KYC status of an application.

    Valid statuses: pending, in_review, approved, rejected
    """
    app = _applications.get(app_id)
    if not app:
        return {"success": False, "error": f"Application {app_id} not found"}

    valid_statuses = ["pending", "in_review", "approved", "rejected"]
    if status not in valid_statuses:
        return {"success": False, "error": f"Invalid status: {status}"}

    app["kyc_status"] = status
    app["reviewed_at"] = datetime.utcnow()

    if status == "approved":
        app["identity_verified"] = True

    return {
        "success": True,
        "application_id": app_id,
        "new_status": status,
        "reviewed_at": app["reviewed_at"].isoformat(),
    }


def verify_identity(app_id: str) -> dict:
    """Simulate identity verification.

    In production, this would call an external KYC provider.
    For the demo, we simulate a quick check.
    """
    app = _applications.get(app_id)
    if not app:
        return {"success": False, "error": f"Application {app_id} not found"}

    # Simulate verification — always passes in demo
    # In production, this would check:
    # 1. Identity document (passport, driving licence)
    # 2. Proof of address
    # 3. Sanctions/PEP screening
    # 4. Electoral roll check

    app["identity_verified"] = True
    app["kyc_status"] = "approved"
    app["reviewed_at"] = datetime.utcnow()

    return {
        "success": True,
        "application_id": app_id,
        "identity_verified": True,
        "checks_passed": [
            "identity_document",
            "proof_of_address",
            "sanctions_screening",
            "electoral_roll",
        ],
    }


def get_onboarding_stats() -> dict:
    """Get statistics on onboarding applications."""
    total = len(_applications)
    pending = sum(1 for a in _applications.values() if a["kyc_status"] == "pending")
    approved = sum(1 for a in _applications.values() if a["kyc_status"] == "approved")
    rejected = sum(1 for a in _applications.values() if a["kyc_status"] == "rejected")

    return {
        "total_applications": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "in_review": total - pending - approved - rejected,
    }
