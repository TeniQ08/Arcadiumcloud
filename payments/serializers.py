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
            "mpesa_receipt_number",
            "transaction_date",
            "result_code",
            "result_description",
            "paid_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
