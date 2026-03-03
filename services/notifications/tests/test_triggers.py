"""Tests for notification triggers."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.notifications.triggers import (
    _alert_configs,
    _notifications,
    check_isa_allowance_trigger,
    check_portfolio_drift_trigger,
    check_price_change_trigger,
    create_notification,
    get_alert_config,
    get_notifications_for_user,
    init_notification_data,
    mark_as_read,
    update_alert_config,
)


@pytest.fixture(autouse=True)
def setup():
    _notifications.clear()
    _alert_configs.clear()
    init_notification_data()


class TestPortfolioDriftTrigger:
    def test_high_drift_triggers(self):
        result = check_portfolio_drift_trigger("user_001", "pf_001", 7.5)
        assert result is not None
        assert result["subject"] == "Portfolio Drift Alert"

    def test_zero_drift_still_triggers(self):
        """Documents bug: 0% drift shouldn't trigger but does."""
        result = check_portfolio_drift_trigger("user_001", "pf_001", 0.0)
        # BUG: should return None but returns a notification
        assert result is not None  # this is the bug


class TestPriceChangeTrigger:
    def test_large_drop_triggers(self):
        result = check_price_change_trigger("user_001", "VOD.L", -12.0, 0.63)
        assert result is not None

    def test_small_change_no_trigger(self):
        result = check_price_change_trigger("user_001", "VOD.L", -2.0, 0.70)
        assert result is None


class TestISAAllowanceTrigger:
    def test_low_allowance_triggers(self):
        result = check_isa_allowance_trigger("user_001", 3000.0, "2024/25")
        assert result is not None

    def test_high_allowance_no_trigger(self):
        result = check_isa_allowance_trigger("user_001", 15000.0, "2024/25")
        assert result is None


class TestNotifications:
    def test_get_user_notifications(self):
        notifications = get_notifications_for_user("user_001")
        assert len(notifications) >= 3

    def test_get_unread_only(self):
        notifications = get_notifications_for_user("user_001", unread_only=True)
        assert all(not n["read"] for n in notifications)

    def test_create_notification(self):
        notif = create_notification(
            user_id="user_001",
            notification_type="email",
            subject="Test",
            body="Test body",
        )
        assert notif["id"] is not None
        assert notif["read"] is False

    def test_mark_as_read(self):
        notifs = get_notifications_for_user("user_001")
        unread = next((n for n in notifs if not n["read"]), None)
        if unread:
            result = mark_as_read(unread["id"])
            assert result["read"] is True


class TestAlertConfig:
    def test_get_config(self):
        config = get_alert_config("user_001")
        assert config["drift_threshold"] == 5.0
        assert config["email_enabled"] is True

    def test_update_config(self):
        config = update_alert_config("user_001", {"drift_threshold": 10.0})
        assert config["drift_threshold"] == 10.0

    def test_default_config_for_new_user(self):
        config = get_alert_config("new_user")
        assert config["drift_threshold"] == 5.0
