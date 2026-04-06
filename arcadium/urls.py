"""URL configuration for the Arcadium project."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("stations.urls")),
    path("api/", include("pricing.urls")),
    path("api/", include("game_sessions.urls")),
    path("api/", include("payments.urls")),
    path("api/", include("devices.urls")),
    path("admin/", admin.site.urls),
]
