from django.db import models
from django.utils import timezone


class Station(models.Model):
    """Physical play station; status drives availability for new sessions."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        IN_USE = "in_use", "In use"
        MAINTENANCE = "maintenance", "Maintenance"
        OFFLINE = "offline", "Offline"

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True,
    )
    pricing_plan = models.ForeignKey(
        "pricing.PricingPlan",
        on_delete=models.PROTECT,
        related_name="stations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["status", "is_active"]),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name
