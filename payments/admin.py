from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("session", "amount_due", "amount_paid", "status", "method", "paid_at")
    list_filter = ("status", "method")
