from django.db import models


class GameSession(models.Model):
    """Gaming session: legacy hourly (post-pay) or prepaid STK flow."""

    class BillingKind(models.TextChoices):
        LEGACY_HOURLY = "legacy_hourly", "Legacy hourly"
        PREPAID_STK = "prepaid_stk", "Prepaid (STK)"

    class Status(models.TextChoices):
        # Legacy hourly
        ACTIVE = "active", "Active"
        PAUSED = "paused", "Paused"
        EXPIRED = "expired", "Expired"
        COMPLETED = "completed", "Completed"
        # Prepaid STK
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAYMENT_FAILED = "payment_failed", "Payment failed"
        PAID = "paid", "Paid"
        ACTIVATION_PENDING = "activation_pending", "Activation pending"
        ACTIVATION_FAILED = "activation_failed", "Activation failed"
        CANCELLED = "cancelled", "Cancelled"

    billing_kind = models.CharField(
        max_length=32,
        choices=BillingKind.choices,
        default=BillingKind.LEGACY_HOURLY,
        db_index=True,
    )

    station = models.ForeignKey(
        "stations.Station",
        on_delete=models.PROTECT,
        related_name="sessions",
    )
    pricing_plan = models.ForeignKey(
        "pricing.PricingPlan",
        on_delete=models.PROTECT,
        related_name="game_sessions",
        null=True,
        blank=True,
        help_text="Selected package for prepaid; optional for legacy (uses station default).",
    )

    opened_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="opened_sessions",
    )
    customer_name = models.CharField(max_length=150, blank=True, default="")
    customer_phone = models.CharField(max_length=20, blank=True, default="")
    game_name = models.CharField(max_length=150, blank=True, default="")

    # Snapshot of plan at sale time (prepaid)
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
        default=Status.ACTIVE,
        db_index=True,
    )

    rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

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
            models.Index(fields=["billing_kind", "status"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.pk} — {self.station} [{self.status}]"


class SessionEvent(models.Model):
    """Append-only audit trail for session lifecycle (especially prepaid)."""

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
