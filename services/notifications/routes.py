"""FastAPI routes for the notifications service."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.notifications.triggers import (
    check_portfolio_drift_trigger,
    check_price_change_trigger,
    get_alert_config,
    get_notifications_for_user,
    init_notification_data,
    mark_as_read,
    update_alert_config,
)

router = APIRouter()

# Initialize sample data
init_notification_data()


class AlertConfigUpdate(BaseModel):
    """Request to update a user's alert configuration."""
    drift_threshold: Optional[float] = Field(
        default=None, description="Portfolio drift percentage to trigger an alert", examples=[5.0]
    )
    price_change_threshold: Optional[float] = Field(
        default=None, description="Price change percentage to trigger an alert", examples=[10.0]
    )
    email_enabled: Optional[bool] = Field(default=None, description="Enable or disable email notifications")
    sms_enabled: Optional[bool] = Field(default=None, description="Enable or disable SMS notifications")
    push_enabled: Optional[bool] = Field(default=None, description="Enable or disable push notifications")


class DriftCheckRequest(BaseModel):
    """Request to check if portfolio drift should trigger a notification."""
    user_id: str = Field(description="ID of the user", examples=["usr_001"])
    portfolio_id: str = Field(description="ID of the portfolio", examples=["pf_001"])
    drift_pct: float = Field(description="Current drift percentage", examples=[5.2])


class PriceCheckRequest(BaseModel):
    """Request to check if a price change should trigger a notification."""
    user_id: str = Field(description="ID of the user", examples=["usr_001"])
    symbol: str = Field(description="Ticker symbol", examples=["VWRL.L"])
    change_pct: float = Field(description="Price change percentage", examples=[-8.5])
    current_price: float = Field(description="Current price in GBP", examples=[75.40])


# --- Routes ---

@router.get("/user/{user_id}", tags=["Notifications - Inbox"], summary="Get user notifications")
async def get_user_notifications(
    user_id: str,
    unread_only: bool = Query(default=False, description="If true, return only unread notifications"),
):
    """Get all notifications for a user.

    Returns a list of notifications, optionally filtered to unread only.
    """
    notifications = get_notifications_for_user(user_id, unread_only=unread_only)
    return {
        "user_id": user_id,
        "notifications": notifications,
        "count": len(notifications),
    }


@router.put("/read/{notification_id}", tags=["Notifications - Inbox"], summary="Mark notification as read")
async def read_notification(notification_id: str):
    """Mark a notification as read.

    Updates the notification's read status to true.
    """
    result = mark_as_read(notification_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
    return result


@router.get("/config/{user_id}", tags=["Notifications - Config"], summary="Get alert configuration")
async def get_config(user_id: str):
    """Get a user's alert configuration.

    Returns the user's current threshold settings and channel preferences.
    """
    return get_alert_config(user_id)


@router.put("/config/{user_id}", tags=["Notifications - Config"], summary="Update alert configuration")
async def update_config(user_id: str, request: AlertConfigUpdate):
    """Update a user's alert configuration.

    Only the fields provided in the request body are updated; omitted fields
    are left unchanged.
    """
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    return update_alert_config(user_id, updates)


@router.post("/check/drift", tags=["Notifications - Triggers"], summary="Check drift trigger")
async def check_drift(request: DriftCheckRequest):
    """Check if portfolio drift should trigger a notification.

    Compares the provided drift percentage against the user's threshold.
    Returns whether a notification was triggered.

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


@router.post("/check/price-change", tags=["Notifications - Triggers"], summary="Check price change trigger")
async def check_price(request: PriceCheckRequest):
    """Check if a price change should trigger a notification.

    Compares the provided price change percentage against the user's threshold.
    Returns whether a notification was triggered.
    """
    result = check_price_change_trigger(
        user_id=request.user_id,
        symbol=request.symbol,
        change_pct=request.change_pct,
        current_price=request.current_price,
    )
    if result:
        return {"triggered": True, "notification": result}
    return {"triggered": False}
