from rest_framework import serializers

from .models import Station


class StationSerializer(serializers.ModelSerializer):
    pricing_plan_name = serializers.CharField(source="pricing_plan.name", read_only=True)
    rate_per_hour = serializers.DecimalField(
        max_digits=8,
        decimal_places=2,
        source="pricing_plan.rate_per_hour",
        read_only=True,
    )
    device = serializers.SerializerMethodField()

    def get_device(self, obj):
        """First registered controller for this station (ordered by device_id)."""
        dev = obj.devices.first()
        if not dev:
            return None
        return {
            "device_id": dev.device_id,
            "status": dev.status,
            "relay_state": dev.relay_state,
            "fault_state": dev.fault_state,
            "last_heartbeat_at": dev.last_heartbeat_at.isoformat() if dev.last_heartbeat_at else None,
        }

    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "status",
            "pricing_plan",
            "is_active",
            "pricing_plan_name",
            "rate_per_hour",
            "device",
        ]
