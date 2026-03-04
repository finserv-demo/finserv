"""Market Data service — price feeds, caching, and retries."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.market_data.routes import router

app = FastAPI(
    title="FinServ Market Data Service",
    description="Market price feeds, caching, and retries",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/market-data", tags=["market-data"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "market-data"}
