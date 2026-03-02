"""Risk Engine service — risk profiling and questionnaire management."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.risk_engine.routes import router
from services.risk_engine.db import init_db

app = FastAPI(
    title="FinServ Risk Engine",
    description="Risk profiling questionnaires and scoring",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/risk", tags=["risk"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "risk-engine"}
