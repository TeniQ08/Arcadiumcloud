from django.urls import path

from . import views

app_name = "stations"

urlpatterns = [
    # Web dashboard
    path("", views.dashboard, name="dashboard"),
    path("stations/<int:station_id>/start/", views.start_session_action, name="start_session"),
    path("sessions/<int:session_id>/pause/", views.pause_session_action, name="pause_session"),
    path("sessions/<int:session_id>/resume/", views.resume_session_action, name="resume_session"),
    path("sessions/<int:session_id>/end/", views.end_session_action, name="end_session"),
    path("sessions/<int:session_id>/extend/", views.extend_session_action, name="extend_session"),

    # API
    path("api/stations/", views.StationListAPIView.as_view(), name="api_station_list"),
]
