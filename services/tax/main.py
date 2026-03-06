"""Tax service — FastAPI application for UK tax calculations."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.tax.routes import router

tags_metadata = [
    {
        "name": "Tax - ISA",
        "description": "Individual Savings Account allowance tracking and contributions.",
    },
    {
        "name": "Tax - CGT",
        "description": "Capital Gains Tax calculations, disposal recording, and annual summaries.",
    },
    {
        "name": "Tax - Harvesting",
        "description": "Tax-loss harvesting opportunity identification.",
    },
    {
        "name": "Tax - General",
        "description": "General tax utilities such as current tax year lookup.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Tax Service",
    description="UK tax calculations including ISA allowance tracking, Capital Gains Tax, "
    "bed-and-breakfasting rule checks, and tax-loss harvesting opportunities.",
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

app.include_router(router, prefix="/api/tax")


@app.get("/health", tags=["Health"], summary="Tax service health check")
async def health():
    """Returns the health status of the tax service."""
    return {"status": "ok", "service": "tax"}
