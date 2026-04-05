"""Centralized clock for testability — patch `TimeService.now` in tests."""

from __future__ import annotations

from django.utils import timezone


class TimeService:
    """Thin wrapper around Django's timezone-aware `now()`."""

    @staticmethod
    def now():
        return timezone.now()
