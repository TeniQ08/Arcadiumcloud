from django.db import transaction
from django.utils import timezone

from .models import GameSession


def _blocking_statuses() -> tuple[str, ...]:
    """Session states that reserve the station until cleared."""
    return (
        GameSession.Status.PENDING_PAYMENT,
        GameSession.Status.ACTIVATION_PENDING,
        GameSession.Status.ACTIVE,
        GameSession.Status.EXPIRED,
    )


def mark_expired_sessions() -> int:
    """
    Mark active sessions past expected_end_time as expired and queue device deactivation.
    """
    from .prepaid_services import queue_deactivate_command

    now = timezone.now()
    expired_candidate_ids = list(
        GameSession.objects.filter(
            status=GameSession.Status.ACTIVE,
            expected_end_time__lt=now,
        ).values_list("pk", flat=True)
    )
    count = 0
    for sid in expired_candidate_ids:
        with transaction.atomic():
            session = GameSession.objects.select_for_update().select_related("station").get(pk=sid)
            if session.status != GameSession.Status.ACTIVE:
                continue
            session.status = GameSession.Status.EXPIRED
            session.expired_at = now
            session.save(update_fields=["status", "expired_at", "updated_at"])
            queue_deactivate_command(session)
            count += 1
    return count
