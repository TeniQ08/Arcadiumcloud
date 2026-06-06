from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "amount_due",
        "amount_paid",
        "status",
        "payment_type",
        "extension_duration_minutes",
        "method",
        "checkout_request_id",
        "response_code",
        "paid_at",
    )
    list_filter = ("status", "payment_type", "method")
    search_fields = (
        "checkout_request_id",
        "merchant_request_id",
        "mpesa_receipt_number",
        "phone_number",
        "mpesa_phone_number",
    )
