"""Onboarding service — KYC, identity verification, and user registration."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.onboarding.routes import router

tags_metadata = [
    {
        "name": "Onboarding - Applications",
        "description": "KYC application submission, retrieval, and status management.",
    },
    {
        "name": "Onboarding - Verification",
        "description": "Identity verification and KYC status updates.",
    },
    {
        "name": "Onboarding - Validation",
        "description": "UK-specific field validation (NI number, postcode, phone).",
    },
    {
        "name": "Onboarding - Stats",
        "description": "Onboarding pipeline statistics.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Onboarding Service",
    description="KYC onboarding, identity verification, and UK-specific field validation. "
    "Handles the full application lifecycle from submission through verification.",
    version="0.1.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/onboarding")


@app.get("/health", tags=["Health"], summary="Onboarding service health check")
async def health():
    """Returns the health status of the onboarding service."""
    return {"status": "ok", "service": "onboarding"}
