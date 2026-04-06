"""Aggregated counts for GET /api/dashboard/summary/."""

from __future__ import annotations

from django.db.models import Count

from devices.models import StationDevice
from game_sessions.models import GameSession
from stations.models import Station


def build_dashboard_summary() -> dict:
    """Return station, session, and device aggregates for the control panel."""
    st = Station.objects.filter(is_active=True)
    station_counts = st.values("status").annotate(n=Count("id"))
    by_status = {row["status"]: row["n"] for row in station_counts}
    total_st = st.count()

    open_qs = GameSession.objects.exclude(
        status__in=(
            GameSession.Status.COMPLETED,
            GameSession.Status.CANCELLED,
            GameSession.Status.PAYMENT_FAILED,
            GameSession.Status.ACTIVATION_FAILED,
        )
    )

    devices = StationDevice.objects.all()
    dev_online = devices.filter(status=StationDevice.Status.ONLINE).count()
    dev_offline = devices.filter(status=StationDevice.Status.OFFLINE).count()
    dev_fault = devices.filter(status=StationDevice.Status.FAULT).count()

    return {
        "stations": {
            "total": total_st,
            "available": by_status.get(Station.Status.AVAILABLE, 0),
            "reserved": by_status.get(Station.Status.RESERVED, 0),
            "in_use": by_status.get(Station.Status.IN_USE, 0),
            "maintenance": by_status.get(Station.Status.MAINTENANCE, 0),
            "offline": by_status.get(Station.Status.OFFLINE, 0),
        },
        "sessions": {
            "open_total": open_qs.count(),
            "pending_payment": open_qs.filter(status=GameSession.Status.PENDING_PAYMENT).count(),
            "activation_pending": open_qs.filter(status=GameSession.Status.ACTIVATION_PENDING).count(),
            "active": open_qs.filter(status=GameSession.Status.ACTIVE).count(),
            "expired": open_qs.filter(status=GameSession.Status.EXPIRED).count(),
        },
        "devices": {
            "online": dev_online,
            "offline": dev_offline,
            "fault": dev_fault,
        },
    }
