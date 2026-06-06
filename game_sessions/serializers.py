from rest_framework import serializers

from .phone_utils import normalize_ke_phone


class CreateStkSessionSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(min_value=1)
    pricing_plan_id = serializers.IntegerField(min_value=1)
    customer_phone = serializers.CharField(max_length=40)
    game_name = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_customer_phone(self, value: str) -> str:
        return normalize_ke_phone(value)


class PaidExtendSessionSerializer(serializers.Serializer):
    pricing_plan_id = serializers.IntegerField(min_value=1, required=False)
    duration_minutes = serializers.IntegerField(min_value=1, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, required=False)
    customer_phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")

    def validate_customer_phone(self, value: str) -> str:
        if not value:
            return ""
        return normalize_ke_phone(value)

    def validate(self, attrs):
        if not attrs.get("pricing_plan_id") and not (attrs.get("duration_minutes") and attrs.get("amount") is not None):
            raise serializers.ValidationError("Provide pricing_plan_id or both duration_minutes and amount.")
        return attrs


class ManualExtendSessionSerializer(serializers.Serializer):
    duration_minutes = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)
