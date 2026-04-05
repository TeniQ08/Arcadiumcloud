from django.urls import path

from . import api_views

urlpatterns = [
    path("sessions/open/", api_views.OpenSessionsAPIView.as_view(), name="api_sessions_open"),
    path("sessions/start/", api_views.StartSessionAPIView.as_view(), name="api_session_start"),
    path("sessions/pause/", api_views.PauseSessionAPIView.as_view(), name="api_session_pause"),
    path("sessions/resume/", api_views.ResumeSessionAPIView.as_view(), name="api_session_resume"),
    path("sessions/end/", api_views.EndSessionAPIView.as_view(), name="api_session_end"),
    path("sessions/extend/", api_views.ExtendSessionAPIView.as_view(), name="api_session_extend"),
]
