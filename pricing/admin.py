from django.contrib import admin

from .models import PricingPlan


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "package_duration_minutes",
        "package_price",
        "pricing_type",
        "is_active",
    )
    list_filter = ("is_active",)
