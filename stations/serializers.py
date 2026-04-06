from rest_framework import serializers

from pricing.models import PricingPlan

from .models import Station


class StationSerializer(serializers.ModelSerializer):
    pricing_plan_name = serializers.CharField(source="pricing_plan.name", read_only=True)
    rate_per_hour = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    device = serializers.SerializerMethodField()

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
            "created_at",
            "updated_at",
        ]

    def get_status(self, obj) -> str:
        """Expose legacy-compatible station status for the dashboard."""
        if obj.status == Station.Status.RESERVED:
            return Station.Status.IN_USE
        if obj.status == Station.Status.OFFLINE:
            return Station.Status.MAINTENANCE
        return obj.status

    def get_rate_per_hour(self, obj):
        """Legacy dashboard expects a numeric string; prepaid packages use package price."""
        plan = obj.pricing_plan
        if plan is None:
            return None
        if plan.plan_kind == PricingPlan.PlanKind.PREPAID_PACKAGE and plan.package_price is not None:
            return str(plan.package_price)
        if plan.rate_per_hour is not None:
            return str(plan.rate_per_hour)
        return "0"

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
