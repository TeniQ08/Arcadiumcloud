from django.contrib import admin

from .models import GameSession, SessionEvent


class SessionEventInline(admin.TabularInline):
    model = SessionEvent
    extra = 0
    readonly_fields = ("event_type", "message", "metadata", "created_at")
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "station",
        "status",
        "start_time",
        "expected_end_time",
        "price_snapshot",
        "created_at",
    )
    list_filter = ("status", "station")
    inlines = [SessionEventInline]


@admin.register(SessionEvent)
class SessionEventAdmin(admin.ModelAdmin):
    list_display = ("session", "event_type", "created_at")
    list_filter = ("event_type",)
