"""Notifications service — email/SMS triggers and threshold alerts."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.notifications.routes import router

tags_metadata = [
    {
        "name": "Notifications - Inbox",
        "description": "Retrieve and manage user notifications.",
    },
    {
        "name": "Notifications - Config",
        "description": "Alert threshold and channel configuration.",
    },
    {
        "name": "Notifications - Triggers",
        "description": "Check whether events (drift, price change) should fire a notification.",
    },
    {
        "name": "Health",
        "description": "Service health checks.",
    },
]

app = FastAPI(
    title="FinServ Notifications Service",
    description="Email/SMS/push notification triggers and threshold-based alerts. "
    "Monitors portfolio drift and price changes to notify users via their preferred channels.",
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

app.include_router(router, prefix="/api/notifications")


@app.get("/health", tags=["Health"], summary="Notifications service health check")
async def health():
    """Returns the health status of the notifications service."""
    return {"status": "ok", "service": "notifications"}
