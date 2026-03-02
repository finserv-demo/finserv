"""Tax service — FastAPI application for UK tax calculations."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.tax.routes import router

app = FastAPI(
    title="FinServ Tax Service",
    description="UK tax calculations: ISA, CGT, bed-and-breakfasting",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/tax", tags=["tax"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tax"}
