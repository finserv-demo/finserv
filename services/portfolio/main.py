"""Portfolio service — FastAPI application for portfolio management and rebalancing."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.portfolio.db import init_db
from services.portfolio.routes import router

tags_metadata = [
    {
        "name": "Portfolio - Holdings",
        "description": "Retrieve portfolios, holdings, and current valuations.",
    },
    {
        "name": "Portfolio - Transactions",
        "description": "Transaction history and paginated queries.",
    },
    {
        "name": "Portfolio - Rebalancing",
        "description": "Drift analysis, target allocation management, and rebalancing execution.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Portfolio Service",
    description="Portfolio management, rebalancing, and holdings tracking. "
    "Provides endpoints for viewing holdings, valuations, transaction history, "
    "drift analysis, and automated rebalancing.",
    version="0.1.0",
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/portfolio")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/health", tags=["Health"], summary="Portfolio service health check")
async def health():
    """Returns the health status of the portfolio service."""
    return {"status": "ok", "service": "portfolio"}
