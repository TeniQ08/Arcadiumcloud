from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0002_daraja_stk_metadata"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("paid", "Paid"),
                    ("success", "Success"),
                    ("failed", "Failed"),
                    ("cancelled", "Cancelled"),
                    ("timeout", "Timeout"),
                ],
                db_index=True,
                default="pending",
                max_length=20,
            ),
        ),
    ]
