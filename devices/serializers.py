from rest_framework import serializers

from .models import DeviceCommand


class DeviceAuthSerializer(serializers.Serializer):
    device_id = serializers.CharField(max_length=100)
    device_secret = serializers.CharField(max_length=255)


class HeartbeatSerializer(DeviceAuthSerializer):
    firmware_version = serializers.CharField(required=False, allow_blank=True, default="")
    ip_address = serializers.IPAddressField(required=False)
    relay_state = serializers.BooleanField(required=False)
    fault_state = serializers.CharField(required=False, allow_blank=True, max_length=100)


class NextCommandQuerySerializer(DeviceAuthSerializer):
    pass


class CommandResultSerializer(DeviceAuthSerializer):
    command_id = serializers.IntegerField(min_value=1)
    status = serializers.CharField(max_length=20)
    result_text = serializers.CharField(required=False, allow_blank=True, default="")


class DeviceCommandListSerializer(serializers.ModelSerializer):
    device_id = serializers.CharField(source="device.device_id", read_only=True)
    station_id = serializers.IntegerField(source="device.station_id", read_only=True)

    class Meta:
        model = DeviceCommand
        fields = [
            "id",
            "device_id",
            "station_id",
            "session",
            "command",
            "status",
            "payload",
            "response_payload",
            "error_message",
            "requested_at",
            "created_at",
            "sent_at",
            "acknowledged_at",
            "completed_at",
            "result_text",
        ]
        read_only_fields = fields


def acknowledge_command_status(raw: str) -> str:
    """Map incoming status string to DeviceCommand.Status value."""
    v = (raw or "").lower()
    if v in {"failed", "error"}:
        return DeviceCommand.Status.FAILED
    return DeviceCommand.Status.ACKNOWLEDGED
