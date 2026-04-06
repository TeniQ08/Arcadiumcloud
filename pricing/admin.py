from django.contrib import admin

from .models import PricingPlan


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "plan_kind",
        "rate_per_hour",
        "package_duration_minutes",
        "package_price",
        "min_duration_minutes",
        "is_active",
    )
    list_filter = ("plan_kind", "is_active")
