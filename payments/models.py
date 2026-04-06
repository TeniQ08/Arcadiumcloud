from decimal import Decimal

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        TIMEOUT = "timeout", "Timeout"

    class Method(models.TextChoices):
        MPESA = "mpesa", "M-Pesa"

    session = models.OneToOneField(
        "game_sessions.GameSession",
        on_delete=models.PROTECT,
        related_name="payment",
    )
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        blank=True,
        default="",
    )
    phone_number = models.CharField(max_length=20, blank=True, default="")

    merchant_request_id = models.CharField(max_length=80, blank=True, default="", db_index=True)
    checkout_request_id = models.CharField(max_length=80, blank=True, default="", db_index=True)
    mpesa_receipt_number = models.CharField(max_length=80, blank=True, default="")
    transaction_date = models.DateTimeField(null=True, blank=True)
    result_code = models.CharField(max_length=32, blank=True, default="")
    result_description = models.TextField(blank=True, default="")
    raw_request_payload = models.JSONField(null=True, blank=True)
    raw_callback_payload = models.JSONField(null=True, blank=True)

    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-session__created_at"]

    def __str__(self) -> str:
        return f"Payment {self.amount_due} ({self.get_status_display()}) — session {self.session_id}"
