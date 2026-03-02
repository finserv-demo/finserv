"""Notification trigger logic — determines when to send notifications.

Handles portfolio drift alerts, price threshold alerts, ISA allowance
reminders, and general system notifications.
"""

import uuid
from datetime import datetime
from typing import Optional


# In-memory store
_notifications: list = []
_alert_configs: dict = {}


# Default thresholds
DEFAULT_DRIFT_THRESHOLD = 5.0  # % portfolio drift before alerting
DEFAULT_PRICE_CHANGE_THRESHOLD = 10.0  # % price change before alerting


def init_notification_data():
    """Initialize sample notification data."""
    _notifications.extend([
        {
            "id": "notif_001",
            "user_id": "user_001",
            "type": "email",
            "subject": "Portfolio Rebalance Completed",
            "body": "Your ISA portfolio has been rebalanced. 3 trades were executed.",
            "sent_at": datetime(2024, 11, 1, 9, 30, 0),
            "read": True,
            "metadata": {"portfolio_id": "pf_001", "trades_count": 3},
        },
        {
            "id": "notif_002",
            "user_id": "user_001",
            "type": "email",
            "subject": "ISA Allowance Reminder",
            "body": "You have £7,500 remaining of your £20,000 ISA allowance for 2024/25. The tax year ends on 5 April 2025.",
            "sent_at": datetime(2024, 11, 15, 10, 0, 0),
            "read": False,
            "metadata": {"remaining_allowance": 7500, "tax_year": "2024/25"},
        },
        {
            "id": "notif_003",
            "user_id": "user_001",
            "type": "sms",
            "subject": "Large Price Movement",
            "body": "VOD.L has dropped 8.5% today. Your holding is now worth £540.",
            "sent_at": datetime(2024, 10, 22, 15, 45, 0),
            "read": True,
            "metadata": {"symbol": "VOD.L", "change_pct": -8.5},
        },
    ])

    # Alert configurations
    _alert_configs["user_001"] = {
        "user_id": "user_001",
        "drift_threshold": DEFAULT_DRIFT_THRESHOLD,
        "price_change_threshold": DEFAULT_PRICE_CHANGE_THRESHOLD,
        "email_enabled": True,
        "sms_enabled": True,
        "push_enabled": False,
    }


def check_portfolio_drift_trigger(
    user_id: str,
    portfolio_id: str,
    drift_pct: float,
) -> Optional[dict]:
    """Check if portfolio drift exceeds the user's alert threshold.

    BUG: This fires a notification even when drift is 0%.
    The condition should be drift_pct > threshold, but it's drift_pct >= 0,
    meaning every drift check (including 0% drift) triggers a notification.
    """
    config = _alert_configs.get(user_id, {})
    threshold = config.get("drift_threshold", DEFAULT_DRIFT_THRESHOLD)

    # BUG: should be `drift_pct > threshold` but condition is wrong
    if drift_pct >= 0:  # BUG: always true for any non-negative drift, including 0%
        notification = create_notification(
            user_id=user_id,
            notification_type="email",
            subject="Portfolio Drift Alert",
            body=f"Your portfolio {portfolio_id} has drifted {drift_pct:.1f}% from target allocations. Consider rebalancing.",
            metadata={
                "portfolio_id": portfolio_id,
                "drift_pct": drift_pct,
                "threshold": threshold,
            },
        )
        return notification

    return None


def check_price_change_trigger(
    user_id: str,
    symbol: str,
    change_pct: float,
    current_price: float,
) -> Optional[dict]:
    """Check if a price change exceeds the user's alert threshold."""
    config = _alert_configs.get(user_id, {})
    threshold = config.get("price_change_threshold", DEFAULT_PRICE_CHANGE_THRESHOLD)

    if abs(change_pct) >= threshold:
        direction = "risen" if change_pct > 0 else "fallen"
        notification = create_notification(
            user_id=user_id,
            notification_type="email",
            subject=f"Price Alert: {symbol}",
            body=f"{symbol} has {direction} {abs(change_pct):.1f}% to £{current_price:.2f}.",
            metadata={
                "symbol": symbol,
                "change_pct": change_pct,
                "current_price": current_price,
            },
        )
        return notification

    return None


def check_isa_allowance_trigger(
    user_id: str,
    remaining_allowance: float,
    tax_year: str,
) -> Optional[dict]:
    """Send a reminder if ISA allowance is running low or near tax year end."""
    # Remind when less than 25% allowance remaining
    if remaining_allowance < 5000:  # hardcoded threshold
        notification = create_notification(
            user_id=user_id,
            notification_type="email",
            subject="ISA Allowance Running Low",
            body=f"You have £{remaining_allowance:,.2f} remaining of your ISA allowance for {tax_year}.",
            metadata={
                "remaining_allowance": remaining_allowance,
                "tax_year": tax_year,
            },
        )
        return notification

    return None


def create_notification(
    user_id: str,
    notification_type: str,
    subject: str,
    body: str,
    metadata: dict = None,
) -> dict:
    """Create and store a new notification.

    BUG: Does not check if the user has opted out of this notification type.
    The email_enabled/sms_enabled flags in the alert config are never checked
    before creating and "sending" a notification.
    """
    # BUG: missing opt-out check — should verify user hasn't disabled this type
    # user config has email_enabled/sms_enabled but we never check it

    notification = {
        "id": f"notif_{uuid.uuid4().hex[:8]}",
        "user_id": user_id,
        "type": notification_type,
        "subject": subject,
        "body": body,
        "sent_at": datetime.utcnow(),
        "read": False,
        "metadata": metadata or {},
    }

    _notifications.append(notification)

    # In production, this would actually send the email/SMS
    _send_notification(notification)

    return notification


def _send_notification(notification: dict):
    """Actually send a notification via the appropriate channel.

    This is a stub — in production it would connect to SendGrid, Twilio, etc.
    """
    # TODO: implement actual sending
    pass


def get_notifications_for_user(user_id: str, unread_only: bool = False) -> list[dict]:
    """Get notifications for a user."""
    notifications = [n for n in _notifications if n["user_id"] == user_id]

    if unread_only:
        notifications = [n for n in notifications if not n["read"]]

    # Sort by sent_at descending
    notifications.sort(key=lambda n: n["sent_at"], reverse=True)

    return notifications


def mark_as_read(notification_id: str) -> Optional[dict]:
    """Mark a notification as read."""
    for notification in _notifications:
        if notification["id"] == notification_id:
            notification["read"] = True
            return notification
    return None


def get_alert_config(user_id: str) -> dict:
    """Get a user's alert configuration."""
    return _alert_configs.get(user_id, {
        "user_id": user_id,
        "drift_threshold": DEFAULT_DRIFT_THRESHOLD,
        "price_change_threshold": DEFAULT_PRICE_CHANGE_THRESHOLD,
        "email_enabled": True,
        "sms_enabled": True,
        "push_enabled": False,
    })


def update_alert_config(user_id: str, updates: dict) -> dict:
    """Update a user's alert configuration."""
    config = get_alert_config(user_id)
    config.update(updates)
    config["user_id"] = user_id
    _alert_configs[user_id] = config
    return config
