from django.db import models


class GameSession(models.Model):
    """Prepaid STK session: pay first, then device activation and timed play."""

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
        ACTIVATION_PENDING = "activation_pending", "Activation pending"
        ACTIVATION_FAILED = "activation_failed", "Activation failed"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    station = models.ForeignKey(
        "stations.Station",
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    pricing_plan = models.ForeignKey(
        "pricing.PricingPlan",
        on_delete=models.PROTECT,
        related_name="game_sessions",
    )

    opened_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="opened_sessions",
    )
    customer_name = models.CharField(max_length=150, blank=True, default="")
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    game_name = models.CharField(max_length=150, blank=True, default="")

    plan_name_snapshot = models.CharField(max_length=150, blank=True, default="")
    pricing_type_snapshot = models.CharField(max_length=50, blank=True, default="")
    duration_minutes_snapshot = models.PositiveIntegerField(null=True, blank=True)
    price_snapshot = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    start_time = models.DateTimeField(null=True, blank=True)
    expected_end_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
        db_index=True,
    )

    notes = models.TextField(blank=True, default="")

    checkout_request_id = models.CharField(max_length=80, blank=True, default="", db_index=True)
    merchant_request_id = models.CharField(max_length=80, blank=True, default="", db_index=True)
    payment_reference = models.CharField(max_length=80, blank=True, default="")

    paid_at = models.DateTimeField(null=True, blank=True)
    activation_requested_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    device_activated_at = models.DateTimeField(null=True, blank=True)
    device_deactivated_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["station", "status"]),
            models.Index(fields=["status", "expected_end_time"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.pk} — {self.station} [{self.status}]"


class SessionEvent(models.Model):
    """Append-only audit trail for session lifecycle."""

    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        PAYMENT_INITIATED = "payment_initiated", "Payment initiated"
        PAYMENT_SUCCESS = "payment_success", "Payment success"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
        ACTIVATION_REQUESTED = "activation_requested", "Activation requested"
        ACTIVATED = "activated", "Activated"
        DEACTIVATION_REQUESTED = "deactivation_requested", "Deactivation requested"
        DEACTIVATED = "deactivated", "Deactivated"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NOTE = "note", "Note"

    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=40, choices=EventType.choices, db_index=True)
    message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at}"
