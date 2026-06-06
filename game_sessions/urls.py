from django.urls import path

from . import api_views

urlpatterns = [
    path("dashboard/summary/", api_views.DashboardSummaryAPIView.as_view(), name="api_dashboard_summary"),
    path("sessions/open/", api_views.OpenSessionsAPIView.as_view(), name="api_sessions_open"),
    path(
        "sessions/<int:pk>/cancel/",
        api_views.CancelSessionAPIView.as_view(),
        name="api_session_cancel",
    ),
    path("sessions/<int:pk>/pause/", api_views.PauseSessionAPIView.as_view(), name="api_session_pause"),
    path("sessions/<int:pk>/resume/", api_views.ResumeSessionAPIView.as_view(), name="api_session_resume"),
    path(
        "sessions/<int:pk>/paid-extend/",
        api_views.PaidExtendSessionAPIView.as_view(),
        name="api_session_paid_extend",
    ),
    path(
        "sessions/<int:pk>/manual-extend/",
        api_views.ManualExtendSessionAPIView.as_view(),
        name="api_session_manual_extend",
    ),
    path("sessions/<int:pk>/", api_views.GameSessionDetailAPIView.as_view(), name="api_session_detail"),
    path("sessions/", api_views.GameSessionListAPIView.as_view(), name="api_sessions_list"),
    path(
        "sessions/create-and-request-payment/",
        api_views.CreateStkSessionAPIView.as_view(),
        name="api_sessions_create_stk",
    ),
]
