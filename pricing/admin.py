from django.contrib import admin

from .models import PricingPlan


@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "rate_per_hour", "min_duration_minutes", "is_active")
    list_filter = ("is_active",)
