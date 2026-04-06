from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from devices.models import DeviceCommand, StationDevice
from stations.models import Station

from .models import GameSession, SessionExtension, SessionPause


def _queue_device_command_if_device_exists(
    station: Station,
    command: str,
    *,
    session: GameSession | None = None,
    payload: dict | None = None,
) -> None:
    """
    Best-effort: enqueue an ESP32 command for the station's first device.

    Never raises: session/payment flows must succeed even if device lookup or
    command creation fails. Command strings remain activate_station / deactivate_station.
    """
    try:
        device = StationDevice.objects.filter(station=station).first()
        if device is None:
            return
        DeviceCommand.objects.create(
            device=device,
            session=session,
            command=command,
            payload=payload or {},
            requested_at=timezone.now(),
        )
    except Exception:
        return


def _require_legacy_session(session: GameSession) -> None:
    if session.billing_kind != GameSession.BillingKind.LEGACY_HOURLY:
        raise ValidationError("This action is only available for legacy hourly sessions.")


def _blocking_statuses() -> tuple[str, ...]:
    return (
        GameSession.Status.ACTIVE,
        GameSession.Status.PAUSED,
        GameSession.Status.EXPIRED,
        GameSession.Status.PENDING_PAYMENT,
        GameSession.Status.PAID,
        GameSession.Status.ACTIVATION_PENDING,
        GameSession.Status.ACTIVATION_FAILED,
    )


def _compute_billable_minutes(session: GameSession) -> int:
    """
    Active (non-paused) minutes elapsed.
    An open pause (resumed_at=None) is treated as still paused until now().
    """
    now = timezone.now()
    end = session.actual_end_time or now

    total_paused = timedelta()
    for pause in session.pauses.all():
        resumed = pause.resumed_at or now
        total_paused += resumed - pause.paused_at

    elapsed = end - session.start_time - total_paused
    return max(0, int(elapsed.total_seconds() / 60))


def _compute_amount_due(session: GameSession) -> Decimal:
    minutes = _compute_billable_minutes(session)
    return (session.rate_per_hour / Decimal("60")) * Decimal(str(minutes))


@transaction.atomic
def start_session(station_id: int, opened_by, duration_minutes: int, customer_name: str = "") -> GameSession:
    """
    Create and activate a session for a station (legacy hourly post-pay).
    Raises ValidationError if the station is unavailable or already has an open session.
    Uses select_for_update to prevent double-booking under concurrent requests.
    """
    if duration_minutes <= 0:
        raise ValidationError("duration_minutes must be greater than zero.")

    station = (
        Station.objects.select_for_update()
        .select_related("pricing_plan")
        .get(pk=station_id, is_active=True)
    )

    plan = station.pricing_plan
    if plan.plan_kind != plan.PlanKind.LEGACY_HOURLY:
        raise ValidationError("This station's default plan is not a legacy hourly plan.")

    if plan.rate_per_hour is None:
        raise ValidationError("Pricing plan is missing rate_per_hour for legacy hourly mode.")

    if duration_minutes < plan.min_duration_minutes:
        raise ValidationError(
            f"Session duration must be at least {plan.min_duration_minutes} minutes for this plan."
        )

    if station.status != Station.Status.AVAILABLE:
        raise ValidationError(f"Station '{station.name}' is not available (status: {station.status}).")

    if station.sessions.filter(status__in=_blocking_statuses()).exists():
        raise ValidationError(f"Station '{station.name}' already has an open session.")

    now = timezone.now()
    session = GameSession.objects.create(
        station=station,
        billing_kind=GameSession.BillingKind.LEGACY_HOURLY,
        opened_by=opened_by,
        customer_name=customer_name,
        start_time=now,
        expected_end_time=now + timedelta(minutes=duration_minutes),
        status=GameSession.Status.ACTIVE,
        rate_per_hour=plan.rate_per_hour,
    )

    station.status = Station.Status.IN_USE
    station.save(update_fields=["status", "updated_at"])

    from payments.models import Payment

    Payment.objects.create(session=session, amount_due=Decimal("0.00"))

    _queue_device_command_if_device_exists(station, DeviceCommand.CommandType.ACTIVATE, session=session)
    return session


@transaction.atomic
def pause_session(session_id: int) -> GameSession:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    _require_legacy_session(session)

    if session.status != GameSession.Status.ACTIVE:
        raise ValidationError("Only active sessions can be paused.")

    session.status = GameSession.Status.PAUSED
    session.save(update_fields=["status", "updated_at"])

    SessionPause.objects.create(session=session, paused_at=timezone.now())
    return session


@transaction.atomic
def resume_session(session_id: int) -> GameSession:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    _require_legacy_session(session)

    if session.status != GameSession.Status.PAUSED:
        raise ValidationError("Only paused sessions can be resumed.")

    open_pause = session.pauses.filter(resumed_at__isnull=True).last()
    if open_pause:
        open_pause.resumed_at = timezone.now()
        open_pause.save(update_fields=["resumed_at"])

    session.status = GameSession.Status.ACTIVE
    session.save(update_fields=["status", "updated_at"])
    return session


@transaction.atomic
def extend_session(session_id: int, additional_minutes: int, extended_by) -> GameSession:
    session = GameSession.objects.select_for_update().get(pk=session_id)
    _require_legacy_session(session)

    if additional_minutes <= 0:
        raise ValidationError("additional_minutes must be greater than zero.")

    allowed = (GameSession.Status.ACTIVE, GameSession.Status.EXPIRED)
    if session.status not in allowed:
        raise ValidationError("Only active or expired sessions can be extended.")

    prev_end = session.expected_end_time
    if prev_end is None:
        raise ValidationError("Session has no expected end time.")

    session.expected_end_time += timedelta(minutes=additional_minutes)

    if session.status == GameSession.Status.EXPIRED:
        session.status = GameSession.Status.ACTIVE

    session.save(update_fields=["expected_end_time", "status", "updated_at"])

    SessionExtension.objects.create(
        session=session,
        extended_by=extended_by,
        previous_end_time=prev_end,
        new_end_time=session.expected_end_time,
        additional_minutes=additional_minutes,
    )
    return session


@transaction.atomic
def end_session(session_id: int) -> GameSession:
    """
    Complete a legacy hourly session regardless of current status (active, paused, or expired).
    Finalises the payment amount_due and frees the station.
    """
    session = (
        GameSession.objects.select_for_update()
        .select_related("station", "payment")
        .get(pk=session_id)
    )
    _require_legacy_session(session)

    if session.status == GameSession.Status.COMPLETED:
        raise ValidationError("Session is already completed.")

    session.pauses.filter(resumed_at__isnull=True).update(resumed_at=timezone.now())

    now = timezone.now()
    session.actual_end_time = now
    session.status = GameSession.Status.COMPLETED
    session.save(update_fields=["actual_end_time", "status", "updated_at"])

    session.payment.amount_due = _compute_amount_due(session)
    session.payment.save(update_fields=["amount_due", "updated_at"])

    session.station.status = Station.Status.AVAILABLE
    session.station.save(update_fields=["status", "updated_at"])

    _queue_device_command_if_device_exists(
        session.station,
        DeviceCommand.CommandType.DEACTIVATE,
        session=session,
    )
    return session


def mark_expired_sessions() -> int:
    """
    Mark expired sessions. Legacy: active -> expired when past expected end.
    Prepaid: active -> expired and queue deactivate_station for hardware.
    """
    now = timezone.now()
    legacy_count = GameSession.objects.filter(
        billing_kind=GameSession.BillingKind.LEGACY_HOURLY,
        status=GameSession.Status.ACTIVE,
        expected_end_time__lt=now,
    ).update(status=GameSession.Status.EXPIRED)

    prepaid_ids = list(
        GameSession.objects.filter(
            billing_kind=GameSession.BillingKind.PREPAID_STK,
            status=GameSession.Status.ACTIVE,
            expected_end_time__lt=now,
        ).values_list("pk", flat=True)
    )
    prepaid_count = 0
    for sid in prepaid_ids:
        with transaction.atomic():
            session = GameSession.objects.select_for_update().select_related("station").get(pk=sid)
            if session.status != GameSession.Status.ACTIVE:
                continue
            session.status = GameSession.Status.EXPIRED
            session.expired_at = now
            session.save(update_fields=["status", "expired_at", "updated_at"])
            from .prepaid_services import queue_deactivate_command

            queue_deactivate_command(session)
            prepaid_count += 1

    return legacy_count + prepaid_count
