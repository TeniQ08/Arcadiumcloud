from decimal import Decimal

from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIAL = "partial", "Partial"
        PAID = "paid", "Paid"

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        MPESA = "mpesa", "M-Pesa"
        CARD = "card", "Card"

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
    )
    method = models.CharField(
        max_length=20,
        choices=Method.choices,
        blank=True,
        default="",
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="collected_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-session__start_time"]

    def __str__(self) -> str:
        return f"Payment {self.amount_due} ({self.get_status_display()}) — session {self.session_id}"
