from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone

from game_sessions.models import GameSession
from payments.models import Payment
from stations.models import Station


PAID_STATUSES = (Payment.Status.PAID, Payment.Status.SUCCESS)
ZERO_MONEY = Value(Decimal("0.00"), output_field=DecimalField(max_digits=12, decimal_places=2))
TERMINAL_SESSION_STATUSES = (
    GameSession.Status.EXPIRED,
    GameSession.Status.COMPLETED,
    GameSession.Status.ACTIVE,
    GameSession.Status.PAUSED,
    GameSession.Status.ACTIVATION_PENDING,
)


@dataclass(frozen=True)
class AnalyticsWindow:
    start: datetime
    end: datetime


def _money(value) -> Decimal:
    return value or Decimal("0.00")


def _minutes(value) -> int:
    return int(value or 0)


def _now() -> datetime:
    return timezone.localtime(timezone.now())


def today_window() -> AnalyticsWindow:
    now = _now()
    start = timezone.make_aware(datetime.combine(now.date(), time.min), timezone.get_current_timezone())
    return AnalyticsWindow(start=start, end=now)


def week_window() -> AnalyticsWindow:
    now = _now()
    start_date = now.date() - timedelta(days=now.weekday())
    start = timezone.make_aware(datetime.combine(start_date, time.min), timezone.get_current_timezone())
    return AnalyticsWindow(start=start, end=now)


def month_window() -> AnalyticsWindow:
    now = _now()
    start = timezone.make_aware(datetime.combine(now.date().replace(day=1), time.min), timezone.get_current_timezone())
    return AnalyticsWindow(start=start, end=now)


def paid_payments():
    return Payment.objects.filter(status__in=PAID_STATUSES).select_related(
        "session",
        "session__station",
        "session__pricing_plan",
    )


def successful_paid_sessions():
    return GameSession.objects.filter(payments__status__in=PAID_STATUSES).distinct()


def payment_time_filter(window: AnalyticsWindow) -> Q:
    return Q(paid_at__gte=window.start, paid_at__lt=window.end) | Q(
        paid_at__isnull=True,
        updated_at__gte=window.start,
        updated_at__lt=window.end,
    )


def revenue_summary() -> dict:
    today = today_window()
    week = week_window()
    month = month_window()
    qs = paid_payments()
    return {
        "today_revenue": _money(qs.filter(payment_time_filter(today)).aggregate(total=Sum("amount_paid"))["total"]),
        "this_week_revenue": _money(qs.filter(payment_time_filter(week)).aggregate(total=Sum("amount_paid"))["total"]),
        "this_month_revenue": _money(qs.filter(payment_time_filter(month)).aggregate(total=Sum("amount_paid"))["total"]),
        "paid_sessions": successful_paid_sessions().count(),
    }


def revenue_by_station() -> list[dict]:
    rows = (
        paid_payments()
        .values("session__station_id", "session__station__name")
        .annotate(total_revenue=Coalesce(Sum("amount_paid"), ZERO_MONEY), paid_sessions=Count("session_id", distinct=True))
        .order_by("-total_revenue", "session__station__name")
    )
    return [
        {
            "station_id": row["session__station_id"],
            "station_name": row["session__station__name"],
            "total_revenue": row["total_revenue"],
            "paid_sessions": row["paid_sessions"],
        }
        for row in rows
    ]


def revenue_by_package() -> list[dict]:
    rows = (
        paid_payments()
        .values("session__pricing_plan_id", "session__plan_name_snapshot", "session__pricing_plan__name")
        .annotate(total_revenue=Coalesce(Sum("amount_paid"), ZERO_MONEY), paid_sessions=Count("session_id", distinct=True))
        .order_by("-total_revenue", "session__pricing_plan__name")
    )
    return [
        {
            "package_id": row["session__pricing_plan_id"],
            "package_name": row["session__plan_name_snapshot"] or row["session__pricing_plan__name"],
            "total_revenue": row["total_revenue"],
            "paid_sessions": row["paid_sessions"],
        }
        for row in rows
    ]


def _session_used_minutes(session: GameSession, *, now: datetime | None = None) -> int:
    now = now or timezone.now()
    if session.duration_minutes_snapshot:
        return int(session.duration_minutes_snapshot)
    if session.start_time and session.actual_end_time:
        return max(0, int((session.actual_end_time - session.start_time).total_seconds() // 60))
    if session.start_time and session.expected_end_time:
        end = min(session.expected_end_time, now)
        return max(0, int((end - session.start_time).total_seconds() // 60))
    return 0


def station_performance() -> list[dict]:
    now = timezone.now()
    revenue_rows = {
        row["session__station_id"]: row
        for row in paid_payments()
        .values("session__station_id")
        .annotate(total_revenue=Coalesce(Sum("amount_paid"), ZERO_MONEY), total_sessions=Count("session_id", distinct=True))
    }
    sessions = successful_paid_sessions().select_related("station")
    used_by_station = defaultdict(int)
    for session in sessions:
        used_by_station[session.station_id] += _session_used_minutes(session, now=now)

    window = month_window()
    elapsed_minutes = max(1, int((window.end - window.start).total_seconds() // 60))
    stations = Station.objects.filter(is_active=True).order_by("name")
    return [
        {
            "station_id": station.id,
            "station_name": station.name,
            "total_sessions": revenue_rows.get(station.id, {}).get("total_sessions", 0),
            "total_revenue": revenue_rows.get(station.id, {}).get("total_revenue", Decimal("0.00")),
            "total_used_minutes": used_by_station.get(station.id, 0),
            "utilization_percentage": round((used_by_station.get(station.id, 0) / elapsed_minutes) * 100, 2),
        }
        for station in stations
    ]


def occupancy(view: str = "daily") -> dict:
    now = _now()
    active_station_count = max(Station.objects.filter(is_active=True).count(), 1)
    if view == "weekly":
        start = week_window().start
        days = 7
    else:
        start = today_window().start
        days = 1
        view = "daily"
    end = now
    total_available_minutes = max(1, int((end - start).total_seconds() // 60) * active_station_count)
    sessions = successful_paid_sessions().filter(created_at__gte=start, created_at__lt=end)
    total_used_minutes = sum(_session_used_minutes(session) for session in sessions)
    buckets = []
    for offset in range(days):
        bucket_start = start + timedelta(days=offset)
        bucket_end = min(bucket_start + timedelta(days=1), end)
        if bucket_start >= end:
            break
        bucket_sessions = sessions.filter(created_at__gte=bucket_start, created_at__lt=bucket_end)
        used = sum(_session_used_minutes(session) for session in bucket_sessions)
        available = max(1, int((bucket_end - bucket_start).total_seconds() // 60) * active_station_count)
        buckets.append(
            {
                "date": bucket_start.date().isoformat(),
                "used_minutes": used,
                "available_minutes": available,
                "occupancy_percentage": round((used / available) * 100, 2),
            }
        )
    return {
        "view": view,
        "total_used_minutes": total_used_minutes,
        "total_available_minutes": total_available_minutes,
        "occupancy_percentage": round((total_used_minutes / total_available_minutes) * 100, 2),
        "buckets": buckets,
    }


def peak_hours() -> list[dict]:
    rows = {
        hour: {"hour": hour, "sessions_count": 0, "revenue": Decimal("0.00"), "used_minutes": 0}
        for hour in range(24)
    }
    for payment in paid_payments():
        session = payment.session
        paid_at = payment.paid_at or payment.updated_at
        hour = timezone.localtime(paid_at).hour
        rows[hour]["sessions_count"] += 1
        rows[hour]["revenue"] += payment.amount_paid or Decimal("0.00")
        rows[hour]["used_minutes"] += _session_used_minutes(session)
    return [rows[hour] for hour in range(24)]
