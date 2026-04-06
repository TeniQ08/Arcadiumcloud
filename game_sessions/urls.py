from django.urls import path

from . import api_views

urlpatterns = [
    path("dashboard/summary/", api_views.DashboardSummaryAPIView.as_view(), name="api_dashboard_summary"),
    path("sessions/open/", api_views.OpenSessionsAPIView.as_view(), name="api_sessions_open"),
    path(
        "sessions/<int:pk>/cancel/",
        api_views.CancelPrepaidSessionAPIView.as_view(),
        name="api_session_cancel_prepaid",
    ),
    path("sessions/<int:pk>/", api_views.GameSessionDetailAPIView.as_view(), name="api_session_detail"),
    path("sessions/", api_views.GameSessionListAPIView.as_view(), name="api_sessions_list"),
    path(
        "sessions/create-and-request-payment/",
        api_views.CreatePrepaidSessionAPIView.as_view(),
        name="api_sessions_create_prepaid",
    ),
    path("sessions/start/", api_views.StartSessionAPIView.as_view(), name="api_session_start"),
    path("sessions/pause/", api_views.PauseSessionAPIView.as_view(), name="api_session_pause"),
    path("sessions/resume/", api_views.ResumeSessionAPIView.as_view(), name="api_session_resume"),
    path("sessions/end/", api_views.EndSessionAPIView.as_view(), name="api_session_end"),
    path("sessions/extend/", api_views.ExtendSessionAPIView.as_view(), name="api_session_extend"),
]
