"""Market Data service — price feeds, caching, and retries."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.market_data.routes import router

tags_metadata = [
    {
        "name": "Market Data - Prices",
        "description": "Real-time and historical price feeds for LSE-listed securities.",
    },
    {
        "name": "Market Data - Symbols",
        "description": "Available symbols and instrument metadata.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Market Data Service",
    description="Market price feeds, caching, and retries for LSE-listed securities. "
    "Provides real-time quotes, historical OHLCV data, and symbol discovery.",
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

app.include_router(router, prefix="/api/market-data")


@app.get("/health", tags=["Health"], summary="Market data health check")
async def health():
    """Returns the health status of the market data service."""
    return {"status": "ok", "service": "market-data"}
