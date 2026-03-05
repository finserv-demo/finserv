"""Risk Engine service — risk profiling and questionnaire management."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.risk_engine.db import init_db
from services.risk_engine.routes import router

tags_metadata = [
    {
        "name": "Risk - Questionnaire",
        "description": "Risk assessment questionnaire retrieval and submission.",
    },
    {
        "name": "Risk - Profile",
        "description": "User risk profiles and recommended allocations.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Risk Engine",
    description="Risk profiling questionnaires, scoring, and recommended portfolio allocations. "
    "Users complete a questionnaire to receive a risk score and tailored allocation.",
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

app.include_router(router, prefix="/api/risk")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health", tags=["Health"], summary="Risk engine health check")
async def health():
    """Returns the health status of the risk engine service."""
    return {"status": "ok", "service": "risk-engine"}
