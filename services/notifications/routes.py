"""FastAPI routes for the notifications service."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.notifications.triggers import (
    get_notifications_for_user,
    mark_as_read,
    get_alert_config,
    update_alert_config,
    check_portfolio_drift_trigger,
    check_price_change_trigger,
    init_notification_data,
)

router = APIRouter()

# Initialize sample data
init_notification_data()


class AlertConfigUpdate(BaseModel):
    drift_threshold: Optional[float] = None
    price_change_threshold: Optional[float] = None
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None


class DriftCheckRequest(BaseModel):
    user_id: str
    portfolio_id: str
    drift_pct: float


class PriceCheckRequest(BaseModel):
    user_id: str
    symbol: str
    change_pct: float
    current_price: float


# --- Routes ---

@router.get("/user/{user_id}")
async def get_user_notifications(user_id: str, unread_only: bool = False):
    """Get all notifications for a user."""
    notifications = get_notifications_for_user(user_id, unread_only=unread_only)
    return {
        "user_id": user_id,
        "notifications": notifications,
        "count": len(notifications),
    }


@router.put("/read/{notification_id}")
async def read_notification(notification_id: str):
    """Mark a notification as read."""
    result = mark_as_read(notification_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
    return result


@router.get("/config/{user_id}")
async def get_config(user_id: str):
    """Get a user's alert configuration."""
    return get_alert_config(user_id)


@router.put("/config/{user_id}")
async def update_config(user_id: str, request: AlertConfigUpdate):
    """Update a user's alert configuration."""
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    return update_alert_config(user_id, updates)


@router.post("/check/drift")
async def check_drift(request: DriftCheckRequest):
    """Check if portfolio drift should trigger a notification.

    BUG: triggers notification even for 0% drift.
    """
    result = check_portfolio_drift_trigger(
        user_id=request.user_id,
        portfolio_id=request.portfolio_id,
        drift_pct=request.drift_pct,
    )
    if result:
        return {"triggered": True, "notification": result}
    return {"triggered": False}


@router.post("/check/price-change")
async def check_price(request: PriceCheckRequest):
    """Check if a price change should trigger a notification."""
    result = check_price_change_trigger(
        user_id=request.user_id,
        symbol=request.symbol,
        change_pct=request.change_pct,
        current_price=request.current_price,
    )
    if result:
        return {"triggered": True, "notification": result}
    return {"triggered": False}
