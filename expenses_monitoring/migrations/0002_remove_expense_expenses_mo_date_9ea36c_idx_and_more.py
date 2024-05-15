# Generated by Django 5.0.6 on 2024-05-12 21:04

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("expenses_monitoring", "0001_initial"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="expense",
            name="expenses_mo_date_9ea36c_idx",
        ),
        migrations.RemoveField(
            model_name="expense",
            name="date",
        ),
        migrations.AddField(
            model_name="expense",
            name="timestamp",
            field=models.BigIntegerField(default=1715547891.675139),
        ),
        migrations.AddIndex(
            model_name="expense",
            index=models.Index(
                fields=["timestamp"], name="expenses_mo_timesta_4439f2_idx"
            ),
        ),
    ]