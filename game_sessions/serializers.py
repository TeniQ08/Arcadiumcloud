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
