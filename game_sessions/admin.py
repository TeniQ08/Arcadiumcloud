from django.contrib import admin

from .models import GameSession, SessionAdjustment, SessionEvent


class SessionEventInline(admin.TabularInline):
    model = SessionEvent
    extra = 0
    readonly_fields = ("event_type", "message", "metadata", "created_at")
    can_delete = False


class SessionAdjustmentInline(admin.TabularInline):
    model = SessionAdjustment
    extra = 0
    readonly_fields = ("adjustment_type", "minutes_added", "reason", "performed_by", "created_at")
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "station",
        "status",
        "start_time",
        "expected_end_time",
        "remaining_seconds_at_pause",
        "price_snapshot",
        "created_at",
    )
    list_filter = ("status", "station")
    inlines = [SessionAdjustmentInline, SessionEventInline]


@admin.register(SessionEvent)
class SessionEventAdmin(admin.ModelAdmin):
    list_display = ("session", "event_type", "created_at")
    list_filter = ("event_type",)


@admin.register(SessionAdjustment)
class SessionAdjustmentAdmin(admin.ModelAdmin):
    list_display = ("session", "adjustment_type", "minutes_added", "performed_by", "created_at")
    list_filter = ("adjustment_type",)
    search_fields = ("session__id", "reason", "performed_by__username")
