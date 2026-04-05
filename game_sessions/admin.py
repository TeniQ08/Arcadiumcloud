from django.contrib import admin

from .models import GameSession, SessionExtension, SessionPause


class SessionPauseInline(admin.TabularInline):
    model = SessionPause
    extra = 0


class SessionExtensionInline(admin.TabularInline):
    model = SessionExtension
    extra = 0


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("station", "status", "start_time", "expected_end_time", "rate_per_hour")
    list_filter = ("status", "station")
    inlines = [SessionPauseInline, SessionExtensionInline]


@admin.register(SessionPause)
class SessionPauseAdmin(admin.ModelAdmin):
    list_display = ("session", "paused_at", "resumed_at")


@admin.register(SessionExtension)
class SessionExtensionAdmin(admin.ModelAdmin):
    list_display = ("session", "previous_end_time", "new_end_time", "additional_minutes", "extended_at")
