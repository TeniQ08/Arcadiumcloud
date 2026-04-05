from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from devices.models import StationDevice
from game_sessions.models import GameSession
from game_sessions.services import (
    end_session,
    extend_session,
    mark_expired_sessions,
    pause_session,
    resume_session,
    start_session,
)
from stations.models import Station

from rest_framework import generics

from .serializers import StationSerializer


def _require_staff_role(request):
    if request.user.role not in (User.Role.ADMIN, User.Role.CASHIER, User.Role.ATTENDANT):
        messages.error(request, "You do not have permission to perform station actions.")
        return redirect("stations:dashboard")
    return None


def _get_open_sessions_by_station():
    open_sessions = (
        GameSession.objects.exclude(status=GameSession.Status.COMPLETED)
        .select_related("station")
        .order_by("-start_time")
    )
    by_station = {}
    for session in open_sessions:
        if session.station_id not in by_station:
            by_station[session.station_id] = session
    return by_station


class StationListAPIView(generics.ListAPIView):
    """
    Read-only list of active stations, ordered by name.
    MVP: no auth/filtering/pagination.
    """

    serializer_class = StationSerializer

    def get_queryset(self):
        return (
            Station.objects.filter(is_active=True)
            .order_by("name")
            .select_related("pricing_plan")
            .prefetch_related(
                Prefetch(
                    "devices",
                    queryset=StationDevice.objects.order_by("device_id"),
                )
            )
        )


def dashboard(request):
    mark_expired_sessions()
    stations = Station.objects.select_related("pricing_plan")
    open_sessions = _get_open_sessions_by_station()
    rows = []
    for station in stations:
        rows.append(
            {
                "station": station,
                "session": open_sessions.get(station.id),
            }
        )
    return render(
        request,
        "stations/dashboard.html",
        {
            "rows": rows,
            "has_stations": bool(rows),
        },
    )


@login_required
@require_POST
def start_session_action(request, station_id: int):
    denied = _require_staff_role(request)
    if denied:
        return denied
    try:
        duration_minutes = int(request.POST.get("duration_minutes", "60"))
        customer_name = request.POST.get("customer_name", "").strip()
        start_session(
            station_id=station_id,
            opened_by=request.user,
            duration_minutes=duration_minutes,
            customer_name=customer_name,
        )
        messages.success(request, "Session started.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, f"Could not start session: {exc}")
    return redirect("stations:dashboard")


@login_required
@require_POST
def pause_session_action(request, session_id: int):
    denied = _require_staff_role(request)
    if denied:
        return denied
    get_object_or_404(GameSession, pk=session_id)
    try:
        pause_session(session_id=session_id)
        messages.success(request, "Session paused.")
    except ValidationError as exc:
        messages.error(request, f"Could not pause session: {exc}")
    return redirect("stations:dashboard")


@login_required
@require_POST
def resume_session_action(request, session_id: int):
    denied = _require_staff_role(request)
    if denied:
        return denied
    get_object_or_404(GameSession, pk=session_id)
    try:
        resume_session(session_id=session_id)
        messages.success(request, "Session resumed.")
    except ValidationError as exc:
        messages.error(request, f"Could not resume session: {exc}")
    return redirect("stations:dashboard")


@login_required
@require_POST
def end_session_action(request, session_id: int):
    denied = _require_staff_role(request)
    if denied:
        return denied
    get_object_or_404(GameSession, pk=session_id)
    try:
        end_session(session_id=session_id)
        messages.success(request, "Session ended.")
    except ValidationError as exc:
        messages.error(request, f"Could not end session: {exc}")
    return redirect("stations:dashboard")


@login_required
@require_POST
def extend_session_action(request, session_id: int):
    denied = _require_staff_role(request)
    if denied:
        return denied
    try:
        additional_minutes = int(request.POST.get("additional_minutes", "15"))
        get_object_or_404(GameSession, pk=session_id)
        extend_session(
            session_id=session_id,
            additional_minutes=additional_minutes,
            extended_by=request.user,
        )
        messages.success(request, "Session extended.")
    except (ValidationError, ValueError) as exc:
        messages.error(request, f"Could not extend session: {exc}")
    return redirect("stations:dashboard")
