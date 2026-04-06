from rest_framework import serializers

from .models import Station


class StationSerializer(serializers.ModelSerializer):
    pricing_plan_name = serializers.CharField(source="pricing_plan.name", read_only=True)
    package_price = serializers.SerializerMethodField()
    package_duration_minutes = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    status_raw = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = [
            "id",
            "name",
            "status",
            "status_raw",
            "pricing_plan",
            "is_active",
            "pricing_plan_name",
            "package_price",
            "package_duration_minutes",
            "device",
            "created_at",
            "updated_at",
        ]

    def get_status(self, obj) -> str:
        """Dashboard-friendly station status (reserved grouped with in-use for badge styling)."""
        if obj.status == Station.Status.RESERVED:
            return Station.Status.IN_USE
        if obj.status == Station.Status.OFFLINE:
            return Station.Status.MAINTENANCE
        return obj.status

    def get_status_raw(self, obj) -> str:
        return obj.status

    def get_package_price(self, obj):
        plan = obj.pricing_plan
        if plan is None:
            return None
        return str(plan.package_price)

    def get_package_duration_minutes(self, obj):
        plan = obj.pricing_plan
        if plan is None:
            return None
        return plan.package_duration_minutes

    def get_device(self, obj):
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
