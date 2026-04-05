from django.db import models


class PricingPlan(models.Model):
    name = models.CharField(max_length=100)
    rate_per_hour = models.DecimalField(max_digits=8, decimal_places=2)
    min_duration_minutes = models.PositiveIntegerField(default=30)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} @ {self.rate_per_hour}/hr"
