from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("analytics/", views.dashboard, name="dashboard"),
    path("api/analytics/revenue/summary/", views.RevenueSummaryAPIView.as_view(), name="api_revenue_summary"),
    path("api/analytics/revenue/by-station/", views.RevenueByStationAPIView.as_view(), name="api_revenue_by_station"),
    path("api/analytics/revenue/by-package/", views.RevenueByPackageAPIView.as_view(), name="api_revenue_by_package"),
    path("api/analytics/stations/performance/", views.StationPerformanceAPIView.as_view(), name="api_station_performance"),
    path("api/analytics/occupancy/", views.OccupancyAPIView.as_view(), name="api_occupancy"),
    path("api/analytics/peak-hours/", views.PeakHoursAPIView.as_view(), name="api_peak_hours"),
]
