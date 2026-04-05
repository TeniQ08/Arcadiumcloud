from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        CASHIER = "cashier", "Cashier"
        ATTENDANT = "attendant", "Attendant"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDANT,
    )

    def __str__(self) -> str:
        return f"{self.get_full_name()} ({self.role})"
