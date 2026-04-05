from django.contrib import admin

from .models import DeviceCommand, StationDevice


@admin.register(StationDevice)
class StationDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_id",
        "station",
        "status",
        "firmware_version",
        "ip_address",
        "last_heartbeat_at",
        "updated_at",
        "relay_state",
        "fault_state",
    )
    list_filter = ("status",)
    search_fields = ("device_id", "station__name")
    readonly_fields = ("last_heartbeat_at", "firmware_version")


@admin.register(DeviceCommand)
class DeviceCommandAdmin(admin.ModelAdmin):
    list_display = ("device", "command", "status", "created_at", "sent_at", "acknowledged_at")
    list_filter = ("status", "command")
    search_fields = ("device__device_id", "device__station__name")
