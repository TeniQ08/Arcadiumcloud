"""Device-side business logic (no Celery — call from views or management commands)."""

from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils.crypto import constant_time_compare
from django.utils import timezone

from .models import DeviceCommand, StationDevice


def authenticate_device(device_id: str, device_secret: str) -> StationDevice | None:
    """
    Return the device if credentials match; uses constant-time secret comparison.

    Missing or whitespace-only id/secret fail closed (no DB hit for empty id).
    """
    did = (device_id or "").strip()
    secret = (device_secret or "").strip()
    if not did or not secret:
        return None
    try:
        device = StationDevice.objects.select_related("station").get(device_id=did)
    except StationDevice.DoesNotExist:
        return None
    if not constant_time_compare(device.device_secret, secret):
        return None
    return device


def _normalize_fault_state(value: str | None) -> str:
    """Normalize fault_state so downstream logic can rely on a stable sentinel value."""
    if value is None:
        return "none"
    s = str(value).strip()
    return s if s else "none"


def apply_heartbeat_fields(device: StationDevice, validated: dict) -> None:
    """
    Apply heartbeat payload to device in memory (caller saves).

    - Always updates last_heartbeat_at.
    - Status mapping (after normalization):
        - ONLINE when fault_state == "none"
        - FAULT otherwise

    Normalization is required because devices/clients may send blank strings or
    omit fields; we treat blank as "none" to avoid false FAULT states.
    """
    device.last_heartbeat_at = timezone.now()

    if "firmware_version" in validated:
        device.firmware_version = validated["firmware_version"]
    if "ip_address" in validated:
        device.ip_address = validated["ip_address"]
    if "relay_state" in validated:
        device.relay_state = validated["relay_state"]
    if "fault_state" in validated:
        device.fault_state = _normalize_fault_state(validated["fault_state"])

    fault_norm = _normalize_fault_state(device.fault_state)
    device.fault_state = fault_norm

    # ONLINE vs FAULT: any non-"none" (after normalization) is considered a fault.
    if fault_norm == "none":
        device.status = StationDevice.Status.ONLINE
    else:
        device.status = StationDevice.Status.FAULT


@transaction.atomic
def mark_offline_devices() -> int:
    """
    Mark devices offline if the last heartbeat is older than 60 seconds.

    Only transitions ONLINE -> OFFLINE (does not alter FAULT).
    """
    cutoff = timezone.now() - timedelta(seconds=60)
    return StationDevice.objects.filter(
        status=StationDevice.Status.ONLINE,
    ).filter(
        last_heartbeat_at__lt=cutoff,
    ).update(status=StationDevice.Status.OFFLINE)


@transaction.atomic
def reset_stale_sent_commands(timeout_seconds: int = 30) -> int:
    """
    Recover commands stuck in SENT (e.g. device rebooted before ACK).

    Sets status back to PENDING and clears sent_at.
    """
    cutoff = timezone.now() - timedelta(seconds=timeout_seconds)
    return DeviceCommand.objects.filter(
        status=DeviceCommand.Status.SENT,
        sent_at__lt=cutoff,
    ).update(status=DeviceCommand.Status.PENDING, sent_at=None)
