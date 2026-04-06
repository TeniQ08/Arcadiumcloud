from __future__ import annotations

import json
import uuid
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from devices.models import DeviceCommand, StationDevice
from payments.models import Payment
from pricing.models import PricingPlan
from stations.models import Station

from .models import GameSession, SessionEvent
from .phone_utils import normalize_ke_phone
from .services import _blocking_statuses


def _log_event(session: GameSession, event_type: str, message: str = "", metadata: dict | None = None) -> None:
    SessionEvent.objects.create(
        session=session,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


def initiate_stk_push_stub(
    *,
    payment: Payment,
    session: GameSession,
    phone: str,
) -> dict[str, Any]:
    """
    Placeholder Daraja STK initiation. Replace with real HTTP call later.
    Returns a dict shaped like a successful Daraja response and persists IDs + raw payload.
    """
    merchant_request_id = f"MR{uuid.uuid4().hex[:16].upper()}"
    checkout_request_id = f"ws_CO_{uuid.uuid4().hex[:24]}"

    raw_request = {
        "MerchantRequestID": merchant_request_id,
        "CheckoutRequestID": checkout_request_id,
        "ResponseCode": "0",
        "ResponseDescription": "Success. Request accepted for processing",
        "PhoneNumber": phone,
        "Amount": str(payment.amount_due),
        "stub": True,
    }

    payment.merchant_request_id = merchant_request_id
    payment.checkout_request_id = checkout_request_id
    payment.phone_number = phone
    payment.method = Payment.Method.MPESA
    payment.raw_request_payload = raw_request
    payment.save(
        update_fields=[
            "merchant_request_id",
            "checkout_request_id",
            "phone_number",
            "method",
            "raw_request_payload",
            "updated_at",
        ]
    )

    session.merchant_request_id = merchant_request_id
    session.checkout_request_id = checkout_request_id
    session.save(update_fields=["merchant_request_id", "checkout_request_id", "updated_at"])

    _log_event(
        session,
        SessionEvent.EventType.PAYMENT_INITIATED,
        "STK push initiated (stub)",
        {"checkout_request_id": checkout_request_id},
    )
    return raw_request


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
    if plan.plan_kind != PricingPlan.PlanKind.PREPAID_PACKAGE:
        raise ValidationError("Selected plan is not a prepaid package.")

    if plan.package_duration_minutes is None or plan.package_price is None:
        raise ValidationError("Prepaid package is missing duration or price.")

    session = GameSession.objects.create(
        station=station,
        billing_kind=GameSession.BillingKind.PREPAID_STK,
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

    initiate_stk_push_stub(payment=payment, session=session, phone=phone)
    return session, payment


def _find_checkout_request_id(payload: dict[str, Any]) -> str | None:
    """Best-effort extraction for Daraja callback JSON shapes."""
    if not payload:
        return None
    if "CheckoutRequestID" in payload:
        return str(payload["CheckoutRequestID"])
    body = payload.get("Body") or {}
    cb = body.get("stkCallback") or body.get("StkCallback") or {}
    if "CheckoutRequestID" in cb:
        return str(cb["CheckoutRequestID"])
    return None


def _find_result_code(payload: dict[str, Any]) -> str | None:
    body = payload.get("Body") or {}
    cb = body.get("stkCallback") or body.get("StkCallback") or {}
    if "ResultCode" in cb:
        return str(cb["ResultCode"])
    if "ResultCode" in payload:
        return str(payload["ResultCode"])
    return None


def _extract_mpesa_receipt(payload: dict[str, Any]) -> str:
    body = payload.get("Body") or {}
    cb = body.get("stkCallback") or body.get("StkCallback") or {}
    meta = cb.get("CallbackMetadata") or {}
    items = meta.get("Item") or []
    for item in items:
        if item.get("Name") == "MpesaReceiptNumber":
            return str(item.get("Value") or "")
    return ""


@transaction.atomic
def handle_stk_callback(*, raw_body: bytes | str) -> Payment | None:
    """
    Parse STK callback payload, update Payment + GameSession, queue activation on success.
    Idempotent: repeated success callbacks do not double-charge state.
    """
    if isinstance(raw_body, bytes):
        text = raw_body.decode("utf-8", errors="replace")
    else:
        text = raw_body

    try:
        payload = json.loads(text) if text else {}
    except json.JSONDecodeError:
        return None

    checkout_id = _find_checkout_request_id(payload)
    if not checkout_id:
        return None

    payment = (
        Payment.objects.select_for_update()
        .select_related("session", "session__station")
        .filter(checkout_request_id=checkout_id)
        .first()
    )
    if payment is None:
        return None

    session = payment.session
    payment.raw_callback_payload = payload
    payment.save(update_fields=["raw_callback_payload", "updated_at"])

    if session.billing_kind != GameSession.BillingKind.PREPAID_STK:
        return payment

    result_code = _find_result_code(payload)
    success = result_code == "0"

    if success and payment.status == Payment.Status.SUCCESS:
        return payment

    if not success:
        payment.status = Payment.Status.FAILED
        payment.result_code = result_code or ""
        payment.result_description = str((payload.get("Body") or {}).get("stkCallback", {}).get("ResultDesc", ""))
        payment.save(
            update_fields=["status", "result_code", "result_description", "raw_callback_payload", "updated_at"]
        )
        session.status = GameSession.Status.PAYMENT_FAILED
        session.save(update_fields=["status", "updated_at"])
        st = session.station
        st.status = Station.Status.AVAILABLE
        st.save(update_fields=["status", "updated_at"])
        _log_event(session, SessionEvent.EventType.PAYMENT_FAILED, "STK payment failed", {"result_code": result_code})
        return payment

    now = timezone.now()
    receipt = _extract_mpesa_receipt(payload)
    payment.status = Payment.Status.SUCCESS
    payment.paid_at = now
    payment.mpesa_receipt_number = receipt
    payment.result_code = result_code or "0"
    payment.result_description = "STK success"
    payment.save(
        update_fields=[
            "status",
            "paid_at",
            "mpesa_receipt_number",
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
    if session.billing_kind != GameSession.BillingKind.PREPAID_STK:
        return None

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
def reconcile_prepaid_device_command(cmd: DeviceCommand) -> None:
    """
    After ESP32 acknowledges a command, advance prepaid session + station state.
    Legacy commands (session is null) are ignored here.
    """
    if cmd.session_id is None:
        return

    session = GameSession.objects.select_for_update().select_related("station").get(pk=cmd.session_id)
    if session.billing_kind != GameSession.BillingKind.PREPAID_STK:
        return

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
