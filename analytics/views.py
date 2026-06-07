from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import STAFF_API_PERMISSIONS, is_staff_role

from . import services
from .serializers import (
    OccupancySerializer,
    PeakHourSerializer,
    RevenueByPackageSerializer,
    RevenueByStationSerializer,
    RevenueSummarySerializer,
    StationPerformanceSerializer,
)


class RevenueSummaryAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        serializer = RevenueSummarySerializer(services.revenue_summary())
        return Response(serializer.data)


class RevenueByStationAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        serializer = RevenueByStationSerializer(services.revenue_by_station(), many=True)
        return Response(serializer.data)


class RevenueByPackageAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        serializer = RevenueByPackageSerializer(services.revenue_by_package(), many=True)
        return Response(serializer.data)


class StationPerformanceAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        serializer = StationPerformanceSerializer(services.station_performance(), many=True)
        return Response(serializer.data)


class OccupancyAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        view = request.query_params.get("view", "daily")
        serializer = OccupancySerializer(services.occupancy(view=view))
        return Response(serializer.data)


class PeakHoursAPIView(APIView):
    permission_classes = STAFF_API_PERMISSIONS

    def get(self, request):
        serializer = PeakHourSerializer(services.peak_hours(), many=True)
        return Response(serializer.data)


@login_required
@user_passes_test(is_staff_role, login_url="/login/")
def dashboard(request):
    return render(request, "analytics/dashboard.html")
