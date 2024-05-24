import logging
from django.core.cache import cache
from datetime import datetime, timedelta
import requests
import time
from .models import Expense, CustomUser, CashType

from celery import shared_task
from .lib import bulk_create_expenses

log = logging.getLogger(__name__)


def fetch_and_update_expenses(user_id, from_time, to_time):
    user = CustomUser.objects.get(id=user_id)
    accounts = user.accounts
    base_url = "https://api.monobank.ua/personal/statement"

    expenses_to_create = []
    for account in accounts:
        log.info(f"Fetching transactions for account {account}")
        time.sleep(61)
        url = f"{base_url}/{account}/{from_time}/{to_time}"
        response = requests.get(url, headers={"X-Token": user.api_key})
        response.raise_for_status()  # Ensure that the request was successful

        transactions = response.json()
        log.info(f"Transactions: {transactions}")
        for transaction in transactions:
            # if transaction['currencyCode'] != '980':
            #     continue
            # if not transaction['hold']:
            # if transaction['currencyCode'] != '980' or transaction['hold']:
            #     log.debug(f"Skipping transaction {transaction['id']} due to filters")
            expenses_to_create.append(
                Expense(
                    user=user,
                    amount=transaction["amount"] / 100.0,
                    cash_type=CashType.objects.get(name="UAH"),
                    timestamp=transaction["time"],
                    description=transaction["description"],
                    expense_type="card_transaction",
                )
            )
            log.info(f"Transaction {transaction['id']} added to the list of expenses")
    log.info(f"Expenses to create: {expenses_to_create}")
    Expense.objects.bulk_create(expenses_to_create)
    log.info(f"Expenses updated for user {user.username}")


def convert_request_to_expense(expenses, user, uah):
    log.info(f"Expenses: {expenses}")
    result = []
    for expanse in expenses:
        log.info(f"Expanse: {expanse}")
        if int(expanse["currencyCode"]) != 980:
            continue
        if expanse["amount"] > 0:
            result.append(
                {
                    "user": user,
                    "amount": expanse["amount"],
                    "cash_type": uah,
                    "timestamp": expanse["time"],
                    "description": expanse["description"],
                    "expense_type": expanse["mcc"],
                }
            )
    return result


def renew_expenses(user, uah):
    expenses = bank.get_new_statements()
    data = convert_request_to_expense(expenses, user, uah)
    if data:
        bulk_create_expenses(data)


@shared_task
def get_previous_month_expenses(bank, user, uah):
    expenses = bank.get_all_statements_for_previous_month()
    data = convert_request_to_expense(expenses, user, uah)
    if expenses:
        bulk_create_expenses(data)


@shared_task
def call_external_api():
    last_call_time = call_external_api.last_call_time
    if last_call_time and (datetime.now() - last_call_time).total_seconds() < 60:
        time_to_wait = 60 - (datetime.now() - last_call_time).total_seconds()
        time.sleep(time_to_wait)
        log.info("Calling the external API")

        call_external_api.last_call_time = datetime.now()
