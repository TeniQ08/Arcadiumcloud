from rest_framework import serializers

from .models import PricingPlan


class PricingPlanListSerializer(serializers.ModelSerializer):
    """Active prepaid packages for cashier UI (additive API)."""

    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "name",
            "plan_kind",
            "pricing_type",
            "package_duration_minutes",
            "package_price",
        ]


class PricingPlanDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "name",
            "plan_kind",
            "pricing_type",
            "package_duration_minutes",
            "package_price",
            "rate_per_hour",
            "min_duration_minutes",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
