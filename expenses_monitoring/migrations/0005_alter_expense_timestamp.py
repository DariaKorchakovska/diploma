# Generated by Django 5.0.6 on 2024-05-14 05:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expenses_monitoring", "0004_alter_expense_timestamp"),
    ]

    operations = [
        migrations.AlterField(
            model_name="expense",
            name="timestamp",
            field=models.BigIntegerField(default=1715663351.095915),
        ),
    ]
