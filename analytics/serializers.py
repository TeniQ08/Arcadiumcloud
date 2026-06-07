from rest_framework import serializers


class RevenueSummarySerializer(serializers.Serializer):
    today_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_week_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    this_month_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_sessions = serializers.IntegerField()


class RevenueByStationSerializer(serializers.Serializer):
    station_id = serializers.IntegerField()
    station_name = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_sessions = serializers.IntegerField()


class RevenueByPackageSerializer(serializers.Serializer):
    package_id = serializers.IntegerField()
    package_name = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    paid_sessions = serializers.IntegerField()


class StationPerformanceSerializer(serializers.Serializer):
    station_id = serializers.IntegerField()
    station_name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_used_minutes = serializers.IntegerField()
    utilization_percentage = serializers.FloatField()


class OccupancySerializer(serializers.Serializer):
    view = serializers.CharField()
    total_used_minutes = serializers.IntegerField()
    total_available_minutes = serializers.IntegerField()
    occupancy_percentage = serializers.FloatField()
    buckets = serializers.ListField(child=serializers.DictField())


class PeakHourSerializer(serializers.Serializer):
    hour = serializers.IntegerField()
    sessions_count = serializers.IntegerField()
    revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    used_minutes = serializers.IntegerField()
