"""
Dashboard JSON compatibility: map internal prepaid/extended statuses to legacy shapes.

The control panel expects station.status in {available, in_use, maintenance} and
session.status in {active, paused, expired} for open sessions (plus completed for closed).
"""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone as dj_tz

from .models import GameSession


def dashboard_station_status(station) -> str:
    """Map internal station status to values the existing dashboard CSS/JS understands."""
    s = station.status
    if s == station.Status.RESERVED:
        return station.Status.IN_USE
    if s == station.Status.OFFLINE:
        return station.Status.MAINTENANCE
    return s


def dashboard_session_status(session: GameSession) -> str:
    """Map internal session status to legacy session badge keys."""
    st = session.status
    if session.billing_kind == GameSession.BillingKind.LEGACY_HOURLY:
        return st

    mapping = {
        GameSession.Status.PENDING_PAYMENT: GameSession.Status.PAUSED,
        GameSession.Status.PAID: GameSession.Status.PAUSED,
        GameSession.Status.ACTIVATION_PENDING: GameSession.Status.PAUSED,
        GameSession.Status.ACTIVE: GameSession.Status.ACTIVE,
        GameSession.Status.EXPIRED: GameSession.Status.EXPIRED,
        GameSession.Status.COMPLETED: GameSession.Status.COMPLETED,
        GameSession.Status.PAYMENT_FAILED: GameSession.Status.EXPIRED,
        GameSession.Status.ACTIVATION_FAILED: GameSession.Status.EXPIRED,
        GameSession.Status.CANCELLED: GameSession.Status.EXPIRED,
    }
    return mapping.get(st, GameSession.Status.PAUSED)


def dashboard_session_payload(session: GameSession) -> dict:
    """
    Keys expected by stations/templates/stations/dashboard.html and game_sessions/api_views.
    """
    start = session.start_time or session.created_at
    start = dj_tz.localtime(start)
    end_display = session.expected_end_time or session.expires_at
    if end_display is not None:
        end_display = dj_tz.localtime(end_display)
    rate = session.rate_per_hour
    if rate is None and session.price_snapshot is not None:
        rate = session.price_snapshot
    if rate is None:
        rate = Decimal("0")

    customer = session.customer_name.strip() if session.customer_name else ""
    if not customer and session.customer_phone:
        customer = session.customer_phone

    expires_iso = session.expires_at.isoformat() if session.expires_at else None
    if not expires_iso and end_display is not None:
        expires_iso = end_display.isoformat()

    return {
        "id": session.id,
        "station_id": session.station_id,
        "opened_by_id": session.opened_by_id,
        "customer_name": customer,
        "start_time": start.isoformat(),
        "expected_end_time": end_display.isoformat() if end_display else None,
        "expires_at": expires_iso,
        "actual_end_time": session.actual_end_time.isoformat() if session.actual_end_time else None,
        "status": dashboard_session_status(session),
        "session_status_raw": session.status,
        "billing_kind": session.billing_kind,
        "game_name": session.game_name or "",
        "rate_per_hour": str(rate),
    }


def open_sessions_queryset():
    """Sessions considered 'open' for the legacy dashboard list."""
    excluded = (
        GameSession.Status.COMPLETED,
        GameSession.Status.CANCELLED,
        GameSession.Status.PAYMENT_FAILED,
    )
    return (
        GameSession.objects.exclude(status__in=excluded)
        .select_related("station")
        .order_by("-created_at")
    )
