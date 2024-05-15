# Generated by Django 5.0.6 on 2024-05-13 21:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "expenses_monitoring",
            "0002_remove_expense_expenses_mo_date_9ea36c_idx_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="bankconnection",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="bankconnection",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="expense",
            name="timestamp",
            field=models.BigIntegerField(default=1715635597.447373),
        ),
        migrations.CreateModel(
            name="Account",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("account_id", models.CharField(max_length=100)),
                ("maskedPan", models.CharField(max_length=100)),
                ("iban", models.CharField(max_length=100)),
                ("currencyCode", models.IntegerField()),
                ("balance", models.FloatField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["user"], name="expenses_mo_user_id_a3b855_idx")
                ],
            },
        ),
    ]
