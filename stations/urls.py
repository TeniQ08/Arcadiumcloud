from django.urls import path

from . import views

app_name = "stations"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/stations/<int:pk>/", views.StationDetailAPIView.as_view(), name="api_station_detail"),
    path("api/stations/", views.StationListAPIView.as_view(), name="api_station_list"),
]
