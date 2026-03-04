"""Notifications service — email/SMS triggers and threshold alerts."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.notifications.routes import router

app = FastAPI(
    title="FinServ Notifications Service",
    description="Email/SMS triggers and threshold alerts",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/notifications", tags=["notifications"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notifications"}
