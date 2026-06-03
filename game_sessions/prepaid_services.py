from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from devices.models import DeviceCommand, StationDevice
from payments.models import Payment
from payments.services.daraja import initiate_stk_push
from pricing.models import PricingPlan
from stations.models import Station

from .models import GameSession, SessionEvent
from .phone_utils import normalize_ke_phone
from .services import _blocking_statuses

logger = logging.getLogger(__name__)

# Daraja STK callbacks are small JSON payloads; reject oversized bodies early.
STK_CALLBACK_MAX_BODY_BYTES = 512 * 1024


def _log_event(session: GameSession, event_type: str, message: str = "", metadata: dict | None = None) -> None:
    SessionEvent.objects.create(
        session=session,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


def request_stk_push(
    *,
    payment: Payment,
    session: GameSession,
    phone: str,
) -> dict[str, Any]:
    """Send a real Daraja STK Push and persist request/response metadata."""
    account_reference = f"ARC{session.pk}"
    response = initiate_stk_push(
        phone_number=phone,
        amount=payment.amount_due,
        account_reference=account_reference,
        transaction_desc=f"Arcadium session {session.pk}",
    )

    payment.merchant_request_id = response.merchant_request_id
    payment.checkout_request_id = response.checkout_request_id
    payment.response_code = response.response_code
    payment.response_description = response.response_description
    payment.customer_message = response.customer_message
    payment.phone_number = phone
    payment.method = Payment.Method.MPESA
    payment.raw_stk_request = response.request_payload
    payment.raw_stk_response = response.response_payload
    payment.raw_request_payload = response.request_payload
    payment.raw_response_payload = response.response_payload
    payment.save(
        update_fields=[
            "merchant_request_id",
            "checkout_request_id",
            "response_code",
            "response_description",
            "customer_message",
            "phone_number",
            "method",
            "raw_stk_request",
            "raw_stk_response",
            "raw_request_payload",
            "raw_response_payload",
            "updated_at",
        ]
    )

    session.merchant_request_id = response.merchant_request_id
    session.checkout_request_id = response.checkout_request_id
    session.save(update_fields=["merchant_request_id", "checkout_request_id", "updated_at"])

    _log_event(
        session,
        SessionEvent.EventType.PAYMENT_INITIATED,
        "STK push initiated",
        {
            "checkout_request_id": response.checkout_request_id,
            "merchant_request_id": response.merchant_request_id,
            "response_code": response.response_code,
        },
    )
    return response.response_payload


@transaction.atomic
def create_session_and_request_payment(
    *,
    station_id: int,
    pricing_plan_id: int,
    customer_phone: str,
    game_name: str = "",
    notes: str = "",
    opened_by=None,
) -> tuple[GameSession, Payment]:
    phone = normalize_ke_phone(customer_phone)

    station = (
        Station.objects.select_for_update()
        .select_related("pricing_plan")
        .get(pk=station_id, is_active=True)
    )
    if station.status != Station.Status.AVAILABLE:
        raise ValidationError(f"Station '{station.name}' is not available for new sales.")

    if station.sessions.filter(status__in=_blocking_statuses()).exists():
        raise ValidationError(f"Station '{station.name}' already has an open session.")

    plan = PricingPlan.objects.select_for_update().get(pk=pricing_plan_id, is_active=True)

    session = GameSession.objects.create(
        station=station,
        pricing_plan=plan,
        opened_by=opened_by,
        customer_phone=phone,
        game_name=game_name or "",
        notes=notes or "",
        plan_name_snapshot=plan.name,
        pricing_type_snapshot=plan.pricing_type or "",
        duration_minutes_snapshot=plan.package_duration_minutes,
        price_snapshot=plan.package_price,
        status=GameSession.Status.PENDING_PAYMENT,
    )

    payment = Payment.objects.create(
        session=session,
        amount_due=plan.package_price,
        amount_paid=Decimal("0.00"),
        status=Payment.Status.PENDING,
        method=Payment.Method.MPESA,
        phone_number=phone,
    )

    station.status = Station.Status.RESERVED
    station.save(update_fields=["status", "updated_at"])

    _log_event(session, SessionEvent.EventType.CREATED, "Prepaid session created")

    request_stk_push(payment=payment, session=session, phone=phone)
    return session, payment


@transaction.atomic
def cancel_session(session_id: int) -> GameSession:
    """Cancel before or while awaiting activation (releases reserved station)."""
    session = GameSession.objects.select_for_update().select_related("station", "payment").get(pk=session_id)

    allowed = {
        GameSession.Status.PENDING_PAYMENT,
        GameSession.Status.ACTIVATION_PENDING,
        GameSession.Status.ACTIVATION_FAILED,
    }
    if session.status not in allowed:
        raise ValidationError("This session cannot be cancelled in its current state.")

    station = session.station
    DeviceCommand.objects.filter(session=session, status=DeviceCommand.Status.PENDING).delete()

    now = timezone.now()
    session.status = GameSession.Status.CANCELLED
    session.completed_at = now
    session.save(update_fields=["status", "completed_at", "updated_at"])

    if station.status == Station.Status.RESERVED:
        station.status = Station.Status.AVAILABLE
        station.save(update_fields=["status", "updated_at"])

    pay = session.payment
    if pay.status == Payment.Status.PENDING:
        pay.status = Payment.Status.CANCELLED
        pay.save(update_fields=["status", "updated_at"])

    _log_event(session, SessionEvent.EventType.CANCELLED, "Session cancelled")
    return session


@transaction.atomic
def retry_stk_push_for_payment(payment_id: int) -> Payment:
    """Re-issue STK Push for a payment still in pending state."""
    payment = Payment.objects.select_for_update().select_related("session").get(pk=payment_id)
    if payment.status != Payment.Status.PENDING:
        raise ValidationError("Only pending payments can retry STK.")
    session = payment.session
    if session.status != GameSession.Status.PENDING_PAYMENT:
        raise ValidationError("Session is not waiting for payment.")
    phone = (payment.phone_number or session.customer_phone or "").strip()
    if not phone:
        raise ValidationError("No phone number on file for this payment.")
    phone = normalize_ke_phone(phone)
    request_stk_push(payment=payment, session=session, phone=phone)
    return payment


def _stk_body_dict(body: Any) -> dict[str, Any]:
    """Safely resolve Body.stkCallback when Body is malformed (not a dict)."""
    if not isinstance(body, dict):
        return {}
    raw = body.get("stkCallback") or body.get("StkCallback")
    if not isinstance(raw, dict):
        return {}
    return raw


def _find_checkout_request_id(payload: dict[str, Any]) -> str | None:
    """Best-effort extraction for Daraja callback JSON shapes."""
    if not payload:
        return None
    if "CheckoutRequestID" in payload:
        return str(payload["CheckoutRequestID"])
    body = payload.get("Body")
    cb = _stk_body_dict(body)
    if "CheckoutRequestID" in cb:
        return str(cb["CheckoutRequestID"])
    return None


def _normalize_checkout_request_id(raw: str | None) -> str | None:
    """Reject empty or oversized IDs (must fit Payment.checkout_request_id)."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or len(s) > 80:
        return None
    return s


def _find_result_code(payload: dict[str, Any]) -> str | None:
    body = payload.get("Body")
    cb = _stk_body_dict(body)
    if "ResultCode" in cb:
        return str(cb["ResultCode"])
    if "ResultCode" in payload:
        return str(payload["ResultCode"])
    return None


def _find_merchant_request_id(payload: dict[str, Any]) -> str:
    body = payload.get("Body")
    cb = _stk_body_dict(body)
    raw = cb.get("MerchantRequestID") or payload.get("MerchantRequestID") or ""
    return str(raw).strip()


def _find_result_desc(payload: dict[str, Any]) -> str:
    body = payload.get("Body")
    cb = _stk_body_dict(body)
    raw = cb.get("ResultDesc") or payload.get("ResultDesc") or ""
    return str(raw).strip()


def _callback_metadata_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    body = payload.get("Body")
    cb = _stk_body_dict(body)
    meta = cb.get("CallbackMetadata") if isinstance(cb.get("CallbackMetadata"), dict) else {}
    if not isinstance(meta, dict):
        return []
    items = meta.get("Item") or []
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _callback_metadata_map(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in _callback_metadata_items(payload):
        name = item.get("Name")
        if name:
            out[str(name)] = item.get("Value")
    return out


def _extract_mpesa_receipt(payload: dict[str, Any]) -> str:
    for item in _callback_metadata_items(payload):
        if item.get("Name") == "MpesaReceiptNumber":
            return str(item.get("Value") or "").strip()
    return ""


def _extract_callback_amount(payload: dict[str, Any]) -> Decimal:
    value = _callback_metadata_map(payload).get("Amount")
    if value in (None, ""):
        return Decimal("0.00")
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except Exception:
        logger.warning("STK callback included invalid Amount metadata")
        return Decimal("0.00")


def _extract_callback_phone(payload: dict[str, Any]) -> str:
    value = _callback_metadata_map(payload).get("PhoneNumber")
    return str(value or "").strip()


def _extract_transaction_date(payload: dict[str, Any]):
    value = _callback_metadata_map(payload).get("TransactionDate")
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.strptime(raw, "%Y%m%d%H%M%S")
    except ValueError:
        logger.warning("STK callback included invalid TransactionDate metadata")
        return None
    return timezone.make_aware(parsed, timezone.get_current_timezone())


@transaction.atomic
def handle_stk_callback(*, raw_body: bytes | str) -> Payment | None:
    """
    Parse STK callback payload, update Payment + GameSession, queue activation on success.
    Idempotent: repeated success callbacks do not double-charge state.

    Malformed or ambiguous callbacks return None without mutating state (fail closed).
    """
    if isinstance(raw_body, bytes):
        text = raw_body.decode("utf-8", errors="replace")
    else:
        text = raw_body

    if len(text) > STK_CALLBACK_MAX_BODY_BYTES:
        logger.warning("STK callback rejected: body exceeds max length")
        return None

    if not text.strip():
        logger.warning("STK callback rejected: empty body")
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("STK callback rejected: invalid JSON")
        return None

    if not isinstance(parsed, dict):
        logger.warning("STK callback rejected: JSON root is not an object")
        return None

    payload: dict[str, Any] = parsed

    checkout_raw = _find_checkout_request_id(payload)
    checkout_id = _normalize_checkout_request_id(checkout_raw)
    if not checkout_id:
        logger.warning("STK callback rejected: missing or invalid CheckoutRequestID")
        return None

    payment = (
        Payment.objects.select_for_update()
        .select_related("session", "session__station")
        .filter(checkout_request_id=checkout_id)
        .first()
    )
    if payment is None:
        logger.warning("STK callback rejected: unknown CheckoutRequestID")
        return None

    session = payment.session

    # Require a parseable ResultCode before any status transition.
    rc_raw = _find_result_code(payload)
    if rc_raw is None:
        logger.warning("STK callback rejected: missing ResultCode")
        return None
    result_code = str(rc_raw).strip()
    if not result_code:
        logger.warning("STK callback rejected: empty ResultCode after strip")
        return None

    merchant_request_id = _find_merchant_request_id(payload)
    result_desc = _find_result_desc(payload)
    payment.raw_callback_payload = payload
    if merchant_request_id and not payment.merchant_request_id:
        payment.merchant_request_id = merchant_request_id
    if checkout_id and not payment.checkout_request_id:
        payment.checkout_request_id = checkout_id
    payment.save(update_fields=["merchant_request_id", "checkout_request_id", "raw_callback_payload", "updated_at"])

    success = result_code == "0"
    paid_statuses = {Payment.Status.PAID, Payment.Status.SUCCESS}

    if payment.status in paid_statuses:
        logger.info("STK callback ignored: payment already processed checkout_request_id=%s", checkout_id)
        return payment

    receipt = _extract_mpesa_receipt(payload)
    if success and receipt:
        existing = (
            Payment.objects.select_for_update()
            .filter(mpesa_receipt_number=receipt, status__in=paid_statuses)
            .exclude(pk=payment.pk)
            .first()
        )
        if existing is not None:
            logger.warning("STK callback ignored: duplicate MpesaReceiptNumber checkout_request_id=%s", checkout_id)
            return existing

    if success and session.status != GameSession.Status.PENDING_PAYMENT:
        logger.info("STK callback ignored: session is no longer pending payment session_id=%s", session.pk)
        return payment

    if not success:
        cancelled = result_code == "1032"
        payment.status = Payment.Status.CANCELLED if cancelled else Payment.Status.FAILED
        payment.result_code = result_code
        payment.result_description = result_desc
        payment.save(
            update_fields=["status", "result_code", "result_description", "raw_callback_payload", "updated_at"]
        )
        session.status = GameSession.Status.CANCELLED if cancelled else GameSession.Status.PAYMENT_FAILED
        session.save(update_fields=["status", "updated_at"])
        st = session.station
        st.status = Station.Status.AVAILABLE
        st.save(update_fields=["status", "updated_at"])
        _log_event(session, SessionEvent.EventType.PAYMENT_FAILED, "STK payment failed", {"result_code": result_code})
        return payment

    now = timezone.now()
    amount_paid = _extract_callback_amount(payload)
    callback_phone = _extract_callback_phone(payload)
    transaction_date = _extract_transaction_date(payload)
    if amount_paid < payment.amount_due:
        payment.status = Payment.Status.FAILED
        payment.amount_paid = amount_paid
        payment.result_code = result_code
        payment.result_description = "STK success amount was less than amount due."
        payment.save(
            update_fields=[
                "status",
                "amount_paid",
                "result_code",
                "result_description",
                "raw_callback_payload",
                "updated_at",
            ]
        )
        session.status = GameSession.Status.PAYMENT_FAILED
        session.save(update_fields=["status", "updated_at"])
        st = session.station
        st.status = Station.Status.AVAILABLE
        st.save(update_fields=["status", "updated_at"])
        _log_event(
            session,
            SessionEvent.EventType.PAYMENT_FAILED,
            "STK payment amount was less than amount due",
            {"amount_paid": str(amount_paid), "amount_due": str(payment.amount_due)},
        )
        return payment

    payment.status = Payment.Status.PAID
    payment.amount_paid = amount_paid
    payment.paid_at = now
    payment.mpesa_receipt_number = receipt
    if callback_phone:
        payment.phone_number = callback_phone
        payment.mpesa_phone_number = callback_phone
    if transaction_date is not None:
        payment.transaction_date = transaction_date
        payment.mpesa_transaction_date = transaction_date
    payment.result_code = result_code
    payment.result_description = result_desc or "STK success"
    payment.save(
        update_fields=[
            "status",
            "amount_paid",
            "paid_at",
            "mpesa_receipt_number",
            "phone_number",
            "mpesa_phone_number",
            "transaction_date",
            "mpesa_transaction_date",
            "result_code",
            "result_description",
            "raw_callback_payload",
            "updated_at",
        ]
    )

    session.status = GameSession.Status.ACTIVATION_PENDING
    session.paid_at = now
    session.payment_reference = receipt or checkout_id
    session.save(update_fields=["status", "paid_at", "payment_reference", "updated_at"])

    _log_event(session, SessionEvent.EventType.PAYMENT_SUCCESS, "Payment confirmed", {"receipt": receipt})

    queue_activate_command(session)
    return payment


@transaction.atomic
def queue_activate_command(session: GameSession) -> DeviceCommand | None:
    station = Station.objects.select_for_update().get(pk=session.station_id)
    device = StationDevice.objects.filter(station=station).first()
    if device is None:
        _log_event(session, SessionEvent.EventType.ACTIVATION_REQUESTED, "No device registered; activation queued logically only")
        session.activation_requested_at = timezone.now()
        session.save(update_fields=["activation_requested_at", "updated_at"])
        return None

    cmd = DeviceCommand.objects.create(
        device=device,
        session=session,
        command=DeviceCommand.CommandType.ACTIVATE,
        payload={"session_id": session.pk},
        requested_at=timezone.now(),
    )
    session.activation_requested_at = timezone.now()
    session.save(update_fields=["activation_requested_at", "updated_at"])
    _log_event(session, SessionEvent.EventType.ACTIVATION_REQUESTED, "Activation command queued", {"command_id": cmd.pk})
    return cmd


@transaction.atomic
def queue_deactivate_command(session: GameSession) -> DeviceCommand | None:
    station = Station.objects.select_for_update().get(pk=session.station_id)
    device = StationDevice.objects.filter(station=station).first()
    if device is None:
        _log_event(session, SessionEvent.EventType.DEACTIVATION_REQUESTED, "No device registered; deactivation skipped")
        return None

    cmd = DeviceCommand.objects.create(
        device=device,
        session=session,
        command=DeviceCommand.CommandType.DEACTIVATE,
        payload={"session_id": session.pk},
        requested_at=timezone.now(),
    )
    _log_event(
        session,
        SessionEvent.EventType.DEACTIVATION_REQUESTED,
        "Deactivation command queued",
        {"command_id": cmd.pk},
    )
    return cmd


@transaction.atomic
def reconcile_session_device_command(cmd: DeviceCommand) -> None:
    """
    After ESP32 acknowledges a command, advance session + station state.
    Commands without session are ignored.
    """
    if cmd.session_id is None:
        return

    session = GameSession.objects.select_for_update().select_related("station").get(pk=cmd.session_id)

    station = session.station
    now = timezone.now()

    if cmd.status == DeviceCommand.Status.FAILED:
        if cmd.command == DeviceCommand.CommandType.ACTIVATE:
            session.status = GameSession.Status.ACTIVATION_FAILED
            session.save(update_fields=["status", "updated_at"])
            station.status = Station.Status.AVAILABLE
            station.save(update_fields=["status", "updated_at"])
        return

    if cmd.status != DeviceCommand.Status.ACKNOWLEDGED:
        return

    if cmd.command == DeviceCommand.CommandType.ACTIVATE:
        if session.status != GameSession.Status.ACTIVATION_PENDING:
            return
        duration = session.duration_minutes_snapshot or 0
        session.status = GameSession.Status.ACTIVE
        session.start_time = now
        session.device_activated_at = now
        session.expected_end_time = now + timedelta(minutes=duration)
        session.expires_at = session.expected_end_time
        session.save(
            update_fields=[
                "status",
                "start_time",
                "device_activated_at",
                "expected_end_time",
                "expires_at",
                "updated_at",
            ]
        )
        station.status = Station.Status.IN_USE
        station.save(update_fields=["status", "updated_at"])
        _log_event(session, SessionEvent.EventType.ACTIVATED, "Station activated", {"command_id": cmd.pk})
        return

    if cmd.command == DeviceCommand.CommandType.DEACTIVATE:
        if session.status not in (GameSession.Status.EXPIRED, GameSession.Status.ACTIVE):
            return
        session.status = GameSession.Status.COMPLETED
        session.actual_end_time = now
        session.completed_at = now
        session.device_deactivated_at = now
        session.save(
            update_fields=[
                "status",
                "actual_end_time",
                "completed_at",
                "device_deactivated_at",
                "updated_at",
            ]
        )
        station.status = Station.Status.AVAILABLE
        station.save(update_fields=["status", "updated_at"])
        _log_event(session, SessionEvent.EventType.COMPLETED, "Session completed after deactivation", {"command_id": cmd.pk})
