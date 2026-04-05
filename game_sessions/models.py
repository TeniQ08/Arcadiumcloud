from django.db import models


class GameSession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"

    station = models.ForeignKey(
        "stations.Station",
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    opened_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="opened_sessions",
    )
    customer_name = models.CharField(max_length=150, blank=True, default="")

    start_time = models.DateTimeField()
    expected_end_time = models.DateTimeField()
    actual_end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2)

    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["station", "status"]),
            models.Index(fields=["status", "expected_end_time"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.pk} — {self.station} [{self.status}]"


class SessionPause(models.Model):
    """Each pause/resume cycle is one record."""

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="pauses",
    )
    paused_at = models.DateTimeField()
    resumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["paused_at"]

    def __str__(self) -> str:
        return f"Pause for session {self.session_id} at {self.paused_at}"


class SessionExtension(models.Model):
    """Audit trail every time a session's end time is pushed."""

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="extensions",
    )
    extended_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="session_extensions",
    )
    previous_end_time = models.DateTimeField()
    new_end_time = models.DateTimeField()
    extended_at = models.DateTimeField(auto_now_add=True)
    additional_minutes = models.PositiveIntegerField()

    class Meta:
        ordering = ["-extended_at"]

    def __str__(self) -> str:
        return f"+{self.additional_minutes}m for session {self.session_id}"
