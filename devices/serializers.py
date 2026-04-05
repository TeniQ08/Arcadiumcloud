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


def acknowledge_command_status(raw: str) -> str:
    """Map incoming status string to DeviceCommand.Status value."""
    v = (raw or "").lower()
    if v in {"failed", "error"}:
        return DeviceCommand.Status.FAILED
    return DeviceCommand.Status.ACKNOWLEDGED
