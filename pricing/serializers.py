from rest_framework import serializers

from .models import PricingPlan


class PricingPlanListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "name",
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
            "pricing_type",
            "package_duration_minutes",
            "package_price",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
