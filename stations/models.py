from django.db import models


class Station(models.Model):
    """Physical play station; status drives availability for new sessions."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        IN_USE = "in_use", "In use"
        MAINTENANCE = "maintenance", "Maintenance"

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    pricing_plan = models.ForeignKey(
        "pricing.PricingPlan",
        on_delete=models.PROTECT,
        related_name="stations",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
