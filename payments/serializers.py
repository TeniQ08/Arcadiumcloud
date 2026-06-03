from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "session",
            "amount_due",
            "amount_paid",
            "status",
            "method",
            "phone_number",
            "merchant_request_id",
            "checkout_request_id",
            "response_code",
            "response_description",
            "customer_message",
            "mpesa_receipt_number",
            "mpesa_transaction_date",
            "mpesa_phone_number",
            "transaction_date",
            "result_code",
            "result_description",
            "raw_stk_request",
            "raw_stk_response",
            "raw_response_payload",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
