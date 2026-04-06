from decimal import Decimal

from django.db import models
from django.utils import timezone


class PricingPlan(models.Model):
    """Sellable time package billed via M-Pesa STK before play."""

    name = models.CharField(max_length=100)
    pricing_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="E.g. time_block, match — informational for reporting.",
    )
    package_duration_minutes = models.PositiveIntegerField()
    package_price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} — {self.package_duration_minutes}m / {self.package_price} KSh"
