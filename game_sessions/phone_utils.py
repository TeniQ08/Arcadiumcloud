"""Kenyan MSISDN normalization for STK (2547XXXXXXXX)."""

from __future__ import annotations

import re

from django.core.exceptions import ValidationError


def normalize_ke_phone(raw: str) -> str:
    """
    Accept 07..., 7..., +254..., 254... and return 2547XXXXXXXX (12 digits after 254).
    """
    s = (raw or "").strip().replace(" ", "")
    if not s:
        raise ValidationError("Phone number is required.")

    digits = re.sub(r"\D", "", s)
    if s.startswith("+"):
        pass  # digits already stripped +

    if digits.startswith("254"):
        rest = digits[3:]
    elif digits.startswith("0") and len(digits) >= 10:
        rest = digits[1:]
    elif digits.startswith("7") and len(digits) >= 9:
        rest = digits
    else:
        raise ValidationError("Unsupported phone format. Use a Kenyan Safaricom number.")

    if len(rest) != 9 or not rest.startswith("7"):
        raise ValidationError("Phone must be 2547XXXXXXXX (9 digits after country code).")

    out = "254" + rest
    if len(out) != 12:
        raise ValidationError("Invalid phone length after normalization.")
    return out
