"""JSON shapes for the control panel and staff session APIs."""

from __future__ import annotations

from decimal import Decimal

from django.utils import timezone as dj_tz

from .models import GameSession


def open_sessions_queryset():
    """Sessions still relevant for station cards (excludes terminal failure/closed states)."""
    excluded = (
        GameSession.Status.COMPLETED,
        GameSession.Status.CANCELLED,
        GameSession.Status.PAYMENT_FAILED,
        GameSession.Status.ACTIVATION_FAILED,
    )
    return (
        GameSession.objects.exclude(status__in=excluded)
        .select_related("station")
        .order_by("-created_at")
    )


def session_payload_for_dashboard(session: GameSession) -> dict:
    """Keys consumed by dashboard.html and game_sessions API list/detail responses."""
    start = session.start_time or session.created_at
    start = dj_tz.localtime(start)
    end_display = session.expected_end_time or session.expires_at
    if end_display is not None:
        end_display = dj_tz.localtime(end_display)

    price_display = session.price_snapshot if session.price_snapshot is not None else Decimal("0")

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
        "status": session.status,
        "game_name": session.game_name or "",
        "package_price": str(price_display),
        "duration_minutes": session.duration_minutes_snapshot,
    }
