from rest_framework import serializers

from .phone_utils import normalize_ke_phone


class StartSessionSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(min_value=1)
    duration_minutes = serializers.IntegerField(min_value=1)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")


class SessionActionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)


class ExtendSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)
    additional_minutes = serializers.IntegerField(min_value=1)


class CreatePrepaidSessionSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(min_value=1)
    pricing_plan_id = serializers.IntegerField(min_value=1)
    customer_phone = serializers.CharField(max_length=40)
    game_name = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_customer_phone(self, value: str) -> str:
        return normalize_ke_phone(value)
