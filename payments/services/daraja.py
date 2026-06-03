from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone

logger = logging.getLogger(__name__)

SANDBOX_OAUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
SANDBOX_STK_PUSH_URL = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
PRODUCTION_OAUTH_URL = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
PRODUCTION_STK_PUSH_URL = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"


@dataclass(frozen=True)
class DarajaStkResponse:
    request_payload: dict[str, Any]
    response_payload: dict[str, Any]
    merchant_request_id: str
    checkout_request_id: str
    response_code: str
    response_description: str
    customer_message: str


def _setting(name: str, *, required: bool = True, default: str = "") -> str:
    value = str(getattr(settings, name, default) or "").strip()
    if required and not value:
        raise ImproperlyConfigured(f"{name} is required for Daraja STK Push.")
    return value


def _urls() -> tuple[str, str]:
    env = _setting("MPESA_ENVIRONMENT", required=False, default="sandbox").lower()
    if env == "sandbox":
        return SANDBOX_OAUTH_URL, SANDBOX_STK_PUSH_URL
    if env == "production":
        return PRODUCTION_OAUTH_URL, PRODUCTION_STK_PUSH_URL
    raise ImproperlyConfigured("MPESA_ENVIRONMENT must be 'sandbox' or 'production'.")


def _post_json(url: str, payload: dict[str, Any], headers: dict[str, str], timeout: int = 30) -> dict[str, Any]:
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        status_code = getattr(exc.response, "status_code", None)
        body = getattr(exc.response, "text", "") or ""
        logger.warning("Daraja HTTP request failed: status=%s body=%s", status_code, body[:500])
        raise ValidationError("Daraja request failed.") from exc

    try:
        parsed = response.json()
    except ValueError as exc:
        logger.warning("Daraja returned invalid JSON: %s", response.text[:500])
        raise ValidationError("Daraja returned invalid JSON.") from exc
    if not isinstance(parsed, dict):
        raise ValidationError("Daraja returned an unexpected response.")
    return parsed


def get_access_token() -> str:
    consumer_key = _setting("MPESA_CONSUMER_KEY")
    consumer_secret = _setting("MPESA_CONSUMER_SECRET")
    oauth_url, _ = _urls()

    credentials = f"{consumer_key}:{consumer_secret}".encode("utf-8")
    auth = base64.b64encode(credentials).decode("ascii")
    try:
        response = requests.get(
            oauth_url,
            headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        status_code = getattr(exc.response, "status_code", None)
        logger.warning("Daraja token request failed: status=%s", status_code)
        raise ValidationError("Could not authenticate with Daraja.") from exc

    try:
        parsed = response.json()
    except ValueError as exc:
        logger.warning("Daraja token response was invalid JSON")
        raise ValidationError("Daraja token response was invalid JSON.") from exc

    token = str(parsed.get("access_token") or "").strip() if isinstance(parsed, dict) else ""
    if not token:
        logger.warning("Daraja token response did not include access_token")
        raise ValidationError("Daraja token response was missing access_token.")
    return token


def generate_stk_password(timestamp: str | None = None) -> tuple[str, str]:
    shortcode = _setting("MPESA_SHORTCODE")
    passkey = _setting("MPESA_PASSKEY")
    ts = timestamp or timezone.localtime(timezone.now()).strftime("%Y%m%d%H%M%S")
    raw = f"{shortcode}{passkey}{ts}".encode("utf-8")
    return base64.b64encode(raw).decode("ascii"), ts


def _normalize_amount(amount: Decimal | int | str) -> int:
    value = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if value <= 0:
        raise ValidationError("STK amount must be greater than zero.")
    return int(value)


def initiate_stk_push(
    phone_number: str,
    amount: Decimal | int | str,
    account_reference: str,
    transaction_desc: str,
) -> DarajaStkResponse:
    shortcode = _setting("MPESA_SHORTCODE")
    callback_url = _setting("MPESA_CALLBACK_URL")
    transaction_type = _setting(
        "MPESA_TRANSACTION_TYPE",
        required=False,
        default="CustomerPayBillOnline",
    )
    _, stk_url = _urls()
    password, timestamp = generate_stk_password()
    token = get_access_token()

    request_payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": transaction_type,
        "Amount": _normalize_amount(amount),
        "PartyA": phone_number,
        "PartyB": shortcode,
        "PhoneNumber": phone_number,
        "CallBackURL": callback_url,
        "AccountReference": str(account_reference)[:12],
        "TransactionDesc": str(transaction_desc)[:100],
    }

    response_payload = _post_json(
        stk_url,
        request_payload,
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    response_code = str(response_payload.get("ResponseCode") or "").strip()
    if response_code and response_code != "0":
        logger.warning("Daraja STK push rejected: response_code=%s", response_code)
        raise ValidationError(response_payload.get("ResponseDescription") or "Daraja STK push was rejected.")

    stored_request_payload = {**request_payload, "Password": "***"}

    return DarajaStkResponse(
        request_payload=stored_request_payload,
        response_payload=response_payload,
        merchant_request_id=str(response_payload.get("MerchantRequestID") or ""),
        checkout_request_id=str(response_payload.get("CheckoutRequestID") or ""),
        response_code=response_code,
        response_description=str(response_payload.get("ResponseDescription") or ""),
        customer_message=str(response_payload.get("CustomerMessage") or ""),
    )
