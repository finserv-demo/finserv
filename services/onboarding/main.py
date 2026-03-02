"""Onboarding service — KYC, identity verification, and user registration."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.onboarding.routes import router

app = FastAPI(
    title="FinServ Onboarding Service",
    description="KYC, identity verification, postcode validation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/onboarding", tags=["onboarding"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "onboarding"}
