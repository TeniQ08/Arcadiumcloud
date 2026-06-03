from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="customer_message",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="payment",
            name="raw_response_payload",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="raw_stk_request",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="raw_stk_response",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="mpesa_phone_number",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="payment",
            name="mpesa_transaction_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="payment",
            name="response_code",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.AddField(
            model_name="payment",
            name="response_description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
