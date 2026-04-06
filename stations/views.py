from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from devices.models import StationDevice
from game_sessions.dashboard_payload import open_sessions_queryset
from stations.models import Station

from rest_framework import generics

from accounts.permissions import STAFF_API_PERMISSIONS

from .serializers import StationSerializer


def _get_open_sessions_by_station():
    open_sessions = open_sessions_queryset()
    by_station = {}
    for session in open_sessions:
        if session.station_id not in by_station:
            by_station[session.station_id] = session
    return by_station


class StationDetailAPIView(generics.RetrieveAPIView):
    """GET /api/stations/<id>/ — single active station (same shape as list rows)."""

    permission_classes = STAFF_API_PERMISSIONS
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


class StationListAPIView(generics.ListAPIView):
    """GET /api/stations/ — active stations for the control panel."""

    permission_classes = STAFF_API_PERMISSIONS
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


@login_required
def dashboard(request):
    from game_sessions.services import mark_expired_sessions

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
