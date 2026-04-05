from django.urls import path

from . import api_views

urlpatterns = [
    path("devices/heartbeat/", api_views.DeviceHeartbeatAPIView.as_view(), name="api_device_heartbeat"),
    path("devices/next-command/", api_views.DeviceNextCommandAPIView.as_view(), name="api_device_next_command"),
    path("devices/command-result/", api_views.DeviceCommandResultAPIView.as_view(), name="api_device_command_result"),
]
