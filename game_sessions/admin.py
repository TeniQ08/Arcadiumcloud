from django.contrib import admin

from .models import GameSession, SessionEvent, SessionExtension, SessionPause


class SessionPauseInline(admin.TabularInline):
    model = SessionPause
    extra = 0


class SessionExtensionInline(admin.TabularInline):
    model = SessionExtension
    extra = 0


class SessionEventInline(admin.TabularInline):
    model = SessionEvent
    extra = 0
    readonly_fields = ("event_type", "message", "metadata", "created_at")
    can_delete = False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "station",
        "billing_kind",
        "status",
        "start_time",
        "expected_end_time",
        "rate_per_hour",
        "created_at",
    )
    list_filter = ("billing_kind", "status", "station")
    inlines = [SessionPauseInline, SessionExtensionInline, SessionEventInline]


@admin.register(SessionEvent)
class SessionEventAdmin(admin.ModelAdmin):
    list_display = ("session", "event_type", "created_at")
    list_filter = ("event_type",)


@admin.register(SessionPause)
class SessionPauseAdmin(admin.ModelAdmin):
    list_display = ("session", "paused_at", "resumed_at")


@admin.register(SessionExtension)
class SessionExtensionAdmin(admin.ModelAdmin):
    list_display = ("session", "previous_end_time", "new_end_time", "additional_minutes", "extended_at")
