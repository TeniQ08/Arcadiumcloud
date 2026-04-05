from django.db import models


class StationDevice(models.Model):
    """A physical controller device associated with a single Station."""

    class Status(models.TextChoices):
        ONLINE = "online", "Online"
        OFFLINE = "offline", "Offline"
        FAULT = "fault", "Fault"

    station = models.ForeignKey("stations.Station", on_delete=models.PROTECT, related_name="devices")
    device_id = models.CharField(max_length=100, unique=True)
    device_secret = models.CharField(max_length=255)
    firmware_version = models.CharField(max_length=50, blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OFFLINE)
    last_heartbeat_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    relay_state = models.BooleanField(default=False)
    fault_state = models.CharField(max_length=100, default="none")

    class Meta:
        ordering = ["device_id"]
        indexes = [
            models.Index(fields=["device_id"], name="devices_sta_devid_idx"),
            models.Index(fields=["status"], name="devices_sta_status_idx"),
            models.Index(fields=["last_heartbeat_at"], name="devices_sta_lasthb_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.device_id} ({self.get_status_display()})"


class DeviceCommand(models.Model):
    """A command queued for a device to execute (ESP32 polls for the next pending command)."""

    class CommandType(models.TextChoices):
        ACTIVATE = "activate_station", "Activate"
        DEACTIVATE = "deactivate_station", "Deactivate"
        WARNING = "warning_mode", "Warning"
        RESET = "reset_fault", "Reset Fault"
        PING = "ping", "Ping"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        ACKNOWLEDGED = "acknowledged", "Acknowledged"
        FAILED = "failed", "Failed"

    device = models.ForeignKey(StationDevice, on_delete=models.CASCADE, related_name="commands")
    command = models.CharField(max_length=32, choices=CommandType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    result_text = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["device"], name="devices_dev_device_idx"),
            models.Index(fields=["status"], name="devices_dev_status_idx"),
            models.Index(fields=["created_at"], name="devices_dev_created_idx"),
            models.Index(fields=["device", "status"], name="devices_dev_dev_stat_idx"),
            models.Index(fields=["device", "status", "created_at"], name="devices_dev_queue_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.command} ({self.get_status_display()}) for {self.device.device_id}"
