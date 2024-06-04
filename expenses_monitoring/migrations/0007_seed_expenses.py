# Generated by Django 5.0.6 on 2024-05-21 13:03

import os
import json
from django.utils import timezone
from expenses_monitoring.models import Expense, CustomUser, CashType
from django.db import migrations


def load_expenses_from_files(user_name, data_directory="data/statements"):
    """
    Load expenses from JSON files and seed the database for the given user.
    """
    user = CustomUser.objects.get(name=user_name)
    cash_type = CashType.objects.get(name="UAH")
    expenses_to_create = []

    for root, dirs, files in os.walk(data_directory):
        for file in files:
            if file.endswith(".json"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    transactions = json.load(f)
                    for transaction in transactions:
                        expenses_to_create.append(
                            Expense(
                                user=user,
                                amount=transaction["amount"] / 100.0,
                                cash_type=cash_type,
                                timestamp=transaction["time"],
                                description=transaction["description"],
                                expense_type=transaction.get("mcc", "Unknown"),  # Adjust this line as needed
                            )
                        )

    Expense.objects.bulk_create(expenses_to_create)
    print(f"Expenses updated for user {user.username}")


# Django migration script to seed data
def create_expenses_from_files(apps, schema_editor):
    CustomUser = apps.get_model("myapp", "CustomUser")
    Expense = apps.get_model("myapp", "Expense")
    CashType = apps.get_model("myapp", "CashType")

    load_expenses_from_files(user_name="daria")  # Replace with appropriate user_id


class Migration(migrations.Migration):
    dependencies = [
        (
            "expenses_monitoring",
            "0006_remove_account_balance_remove_account_currencycode_and_more",
        ),
    ]

    operations = []
