from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, override_settings

from devices.models import DeviceCommand, StationDevice
from game_sessions.models import GameSession
from game_sessions.prepaid_services import handle_stk_callback
from payments.models import Payment
from payments.services.daraja import initiate_stk_push
from pricing.models import PricingPlan
from stations.models import Station


def stk_callback_payload(
    *,
    result_code: int,
    checkout_request_id: str = "ws_CO_123",
    merchant_request_id: str = "MR_123",
    receipt: str = "TST123ABC",
) -> dict:
    callback = {
        "MerchantRequestID": merchant_request_id,
        "CheckoutRequestID": checkout_request_id,
        "ResultCode": result_code,
        "ResultDesc": "The service request is processed successfully." if result_code == 0 else "Request cancelled by user.",
    }
    if result_code == 0:
        callback["CallbackMetadata"] = {
            "Item": [
                {"Name": "Amount", "Value": 100},
                {"Name": "MpesaReceiptNumber", "Value": receipt},
                {"Name": "TransactionDate", "Value": 20260603123045},
                {"Name": "PhoneNumber", "Value": 254712345678},
            ]
        }
    return {"Body": {"stkCallback": callback}}


class DarajaServiceTests(TestCase):
    @override_settings(
        MPESA_ENVIRONMENT="sandbox",
        MPESA_CONSUMER_KEY="test-key",
        MPESA_CONSUMER_SECRET="test-secret",
        MPESA_SHORTCODE="123456",
        MPESA_PASSKEY="test-passkey",
        MPESA_CALLBACK_URL="https://example.com/api/payments/stk-callback/",
        MPESA_TRANSACTION_TYPE="CustomerPayBillOnline",
    )
    @patch("payments.services.daraja.get_access_token", return_value="token")
    @patch("payments.services.daraja._post_json")
    def test_initiate_stk_push_builds_request_and_returns_metadata(self, post_json, _token):
        post_json.return_value = {
            "MerchantRequestID": "MR_123",
            "CheckoutRequestID": "ws_CO_123",
            "ResponseCode": "0",
            "ResponseDescription": "Success. Request accepted for processing",
            "CustomerMessage": "Success. Request accepted for processing",
        }

        response = initiate_stk_push(
            phone_number="254712345678",
            amount=Decimal("100.00"),
            account_reference="ARC1",
            transaction_desc="Arcadium session 1",
        )

        sent_payload = post_json.call_args.args[1]
        self.assertEqual(sent_payload["BusinessShortCode"], "123456")
        self.assertEqual(sent_payload["TransactionType"], "CustomerPayBillOnline")
        self.assertEqual(sent_payload["Amount"], 100)
        self.assertEqual(sent_payload["PhoneNumber"], "254712345678")
        self.assertEqual(response.checkout_request_id, "ws_CO_123")
        self.assertEqual(response.request_payload["Password"], "***")


class StkCallbackTests(TestCase):
    def setUp(self):
        self.plan = PricingPlan.objects.create(
            name="1 Hour",
            package_duration_minutes=60,
            package_price=Decimal("100.00"),
            is_active=True,
        )
        self.station = Station.objects.create(
            name="PS5-01",
            pricing_plan=self.plan,
            status=Station.Status.RESERVED,
        )
        self.device = StationDevice.objects.create(
            station=self.station,
            device_id="esp32-01",
            device_secret="secret",
        )
        self.session = GameSession.objects.create(
            station=self.station,
            pricing_plan=self.plan,
            customer_phone="254712345678",
            plan_name_snapshot=self.plan.name,
            duration_minutes_snapshot=self.plan.package_duration_minutes,
            price_snapshot=self.plan.package_price,
            checkout_request_id="ws_CO_123",
            merchant_request_id="MR_123",
            status=GameSession.Status.PENDING_PAYMENT,
        )
        self.payment = Payment.objects.create(
            session=self.session,
            amount_due=Decimal("100.00"),
            status=Payment.Status.PENDING,
            method=Payment.Method.MPESA,
            phone_number="254712345678",
            checkout_request_id="ws_CO_123",
            merchant_request_id="MR_123",
        )

    def post_callback(self, payload: dict) -> Payment | None:
        return handle_stk_callback(raw_body=json.dumps(payload))

    def test_successful_callback_marks_paid_and_queues_activation(self):
        payment = self.post_callback(stk_callback_payload(result_code=0))

        self.assertIsNotNone(payment)
        self.payment.refresh_from_db()
        self.session.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(self.payment.amount_paid, Decimal("100.00"))
        self.assertEqual(self.payment.mpesa_receipt_number, "TST123ABC")
        self.assertEqual(self.payment.phone_number, "254712345678")
        self.assertEqual(self.payment.mpesa_phone_number, "254712345678")
        self.assertIsNotNone(self.payment.transaction_date)
        self.assertIsNotNone(self.payment.mpesa_transaction_date)
        self.assertEqual(self.session.status, GameSession.Status.ACTIVATION_PENDING)
        self.assertEqual(DeviceCommand.objects.count(), 1)
        self.assertEqual(DeviceCommand.objects.get().command, DeviceCommand.CommandType.ACTIVATE)

    def test_cancelled_callback_marks_cancelled_and_does_not_activate(self):
        payment = self.post_callback(stk_callback_payload(result_code=1032))

        self.assertIsNotNone(payment)
        self.payment.refresh_from_db()
        self.session.refresh_from_db()
        self.station.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.CANCELLED)
        self.assertEqual(self.session.status, GameSession.Status.CANCELLED)
        self.assertEqual(self.station.status, Station.Status.AVAILABLE)
        self.assertEqual(DeviceCommand.objects.count(), 0)

    def test_duplicate_success_callback_does_not_queue_duplicate_activation(self):
        payload = stk_callback_payload(result_code=0)

        self.post_callback(payload)
        self.post_callback(payload)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.PAID)
        self.assertEqual(DeviceCommand.objects.count(), 1)
