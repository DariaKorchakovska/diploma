import time
from datetime import datetime, timedelta, timezone
import logging

from exp_d.settings import MMC
from django.db import transaction
import requests

from django.core.exceptions import ObjectDoesNotExist

from expenses_monitoring.models import CashType, Expense, CustomUser, Account

log = logging.getLogger(__name__)


def fetch_and_update_expenses(user_id, from_time, to_time):
    """ Fetch and update expenses from the MonoBank API. """

    user = CustomUser.objects.get(id=user_id)
    accounts = user.accounts
    base_url = 'https://api.monobank.ua/personal/statement'

    expenses_to_create = []
    for account in accounts:
        log.info(f"Fetching transactions for account {account}")
        time.sleep(61)
        url = f"{base_url}/{account}/{from_time}/{to_time}"
        response = requests.get(url, headers={'X-Token': user.api_key})
        response.raise_for_status()  # Ensure that the request was successful

        transactions = response.json()
        log.info(f"Transactions: {transactions}")
        for transaction in transactions:
            expenses_to_create.append(Expense(
                user=user,
                amount=transaction['amount'] / 100.0,
                cash_type=CashType.objects.get(name='UAH'),
                timestamp=transaction['time'],
                description=transaction['description'],
                expense_type=MMC.get(str(transaction['mcc']))
            ))
            log.info(f"Transaction {transaction['id']} added to the list of expenses")
    log.info(f"Expenses to create: {expenses_to_create}")
    Expense.objects.bulk_create(expenses_to_create)
    log.info(f"Expenses updated for user {user.username}")


def fetch_client_info(api_key):
    """ Fetch the client information from the MonoBank API. """
    url = "https://api.monobank.ua/personal/client-info"
    headers = {'X-Token': api_key}
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raises an HTTPError for bad requests
    return response.json()


def update_or_create_accounts(user, data):
    """ Update or create accounts based on fetched API data. """

    if 'accounts' in data:
        with transaction.atomic():
            for account_data in data['accounts']:
                account, created = Account.objects.update_or_create(
                    user=user,
                    account_id=account_data['id'],  # Use the account ID to identify the account
                    defaults={
                        'maskedPan': account_data['maskedPan'][0] if account_data.get('maskedPan') else '',
                        'iban': account_data['iban'],
                        'currencyCode': account_data['currencyCode'],
                        'balance': account_data['balance']
                    }
                )


def sync_user_accounts(user):
    """ Synchronize the user's bank accounts with the MonoBank API. """
    try:
        client_info = fetch_client_info(user.api_key)
        log.info(f"Fetched client info: {client_info}")
        update_or_create_accounts(user, client_info)
        log.info("Accounts updated successfully")
    except requests.RequestException as e:
        log.error(f"Failed to fetch data from MonoBank API: {str(e)}")
    except Exception as e:
        log.error(f"An error occurred while updating accounts: {str(e)}")



def get_latest_expense_timestamp():
    """
    Get the timestamp of the latest expense in the database.

    Returns:
        The timestamp of the latest expense, or None if there are no expenses.
    """
    try:
        latest_expense = Expense.objects.order_by('-timestamp').first()
        if latest_expense is not None:
            return latest_expense.timestamp
        else:
            return None
    except ObjectDoesNotExist:
        return None


def get_previous_month_time_bounds():
    """
    Get the time bounds for the previous month.

    Returns:
        A tuple of two integers representing the start and end of the previous month.
    """
    now = datetime.now()
    first_day_of_current_month = datetime(now.year, now.month, 1)
    first_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = datetime(
        first_day_of_previous_month.year,
        first_day_of_previous_month.month,
        1
    )
    last_day_of_previous_month = first_day_of_current_month - timedelta(seconds=1)
    start_of_previous_month = int(first_day_of_previous_month.replace(tzinfo=timezone.utc).timestamp())
    end_of_previous_month = int(last_day_of_previous_month.replace(tzinfo=timezone.utc).timestamp())

    return start_of_previous_month, end_of_previous_month


def get_current_month_time_bounds():
    """
    Get the time bounds for the current month.

    Returns:
        A tuple of two integers representing the start and end of the current month.
    """
    now = datetime.now()
    first_day_of_current_month = datetime(now.year, now.month, 1)
    start_of_current_month = int(first_day_of_current_month.replace(tzinfo=timezone.utc).timestamp())
    current_time = int(now.replace(tzinfo=timezone.utc).timestamp())

    return start_of_current_month, current_time


def get_latest_bounds():
    """
    Get the time bounds for the latest expense in the database.

    Returns:
        A tuple of two integers representing the start and end of the latest expense.
    """
    now = datetime.now()
    latest_timestamp = get_latest_expense_timestamp()
    current_time = int(now.replace(tzinfo=timezone.utc).timestamp())
    if latest_timestamp is None:
        return get_current_month_time_bounds()
    return latest_timestamp, current_time
