"""Portfolio service — FastAPI application for portfolio management and rebalancing."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.portfolio.routes import router
from services.portfolio.db import init_db

app = FastAPI(
    title="FinServ Portfolio Service",
    description="Portfolio management, rebalancing, and holdings tracking",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/portfolio", tags=["portfolio"])


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "portfolio"}
