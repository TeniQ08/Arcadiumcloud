from decimal import Decimal

from django.db import models
from django.utils import timezone


class PricingPlan(models.Model):
    """Pricing plan: legacy hourly (post-pay) or fixed prepaid package."""

    class PlanKind(models.TextChoices):
        LEGACY_HOURLY = "legacy_hourly", "Legacy hourly"
        PREPAID_PACKAGE = "prepaid_package", "Prepaid package"

    name = models.CharField(max_length=100)
    plan_kind = models.CharField(
        max_length=32,
        choices=PlanKind.choices,
        default=PlanKind.LEGACY_HOURLY,
        db_index=True,
    )
    # Legacy hourly (post-pay): used with station default plan + start_session().
    rate_per_hour = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Legacy hourly rate; null for pure prepaid package rows.",
    )
    min_duration_minutes = models.PositiveIntegerField(default=30)
    # Prepaid fixed packages (STK): duration + total price in KSh.
    pricing_type = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="E.g. time_block, match — informational for reporting.",
    )
    package_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    package_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=None,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["plan_kind", "is_active"]),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        if self.plan_kind == self.PlanKind.PREPAID_PACKAGE and self.package_price is not None:
            return f"{self.name} — {self.package_duration_minutes}m / {self.package_price} KSh"
        rate = self.rate_per_hour if self.rate_per_hour is not None else Decimal("0")
        return f"{self.name} @ {rate}/hr"
