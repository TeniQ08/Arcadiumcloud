from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Payment


@transaction.atomic
def record_payment(session_id: int, amount: Decimal, method: str, collected_by) -> Payment:
    """
    Record a full or partial payment against a completed session.
    Raises if the session is not yet completed (amount_due not finalised).
    """
    payment = Payment.objects.select_for_update().select_related("session").get(session_id=session_id)

    if payment.session.status != "completed":
        raise ValidationError("Cannot accept payment before the session is completed.")

    if payment.status == Payment.Status.PAID:
        raise ValidationError("This session is already fully paid.")

    payment.amount_paid += amount
    payment.method = method
    payment.collected_by = collected_by

    if payment.amount_paid >= payment.amount_due:
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
    else:
        payment.status = Payment.Status.PARTIAL

    payment.save()
    return payment
