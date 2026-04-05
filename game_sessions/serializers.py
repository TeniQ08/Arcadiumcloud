from rest_framework import serializers


class StartSessionSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(min_value=1)
    duration_minutes = serializers.IntegerField(min_value=1)
    customer_name = serializers.CharField(required=False, allow_blank=True, default="")


class SessionActionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)


class ExtendSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(min_value=1)
    additional_minutes = serializers.IntegerField(min_value=1)
