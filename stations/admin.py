from django.contrib import admin

from .models import Station


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "pricing_plan", "created_at")
    list_filter = ("status", "pricing_plan")
