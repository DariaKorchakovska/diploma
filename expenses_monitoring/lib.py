import json
import os
import time
from datetime import datetime, timedelta, timezone
import logging

from exp_d import settings
from exp_d.settings import MMC
from django.db import transaction
import requests

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from django.core.exceptions import ObjectDoesNotExist

from expenses_monitoring.models import CashType, Expense, CustomUser, Account

log = logging.getLogger(__name__)


def fetch_and_update_expenses(user, from_time, to_time):
    """ Fetch and update expenses from the MonoBank API. """

    accounts = user.accounts
    base_url = 'https://api.monobank.ua/personal/statement'

    expenses_to_create = []
    for account in accounts:
        log.info(f"Fetching transactions for account {account}")
        time.sleep(61)
        url = f"{base_url}/{account}/{from_time}/{to_time}"
        response = requests.get(url, headers={'X-Token': user.api_key})
        response.raise_for_status()  # Ensure that the request was successful

        users_transactions = response.json()
        log.info(f"Transactions: {users_transactions}")
        for users_transaction in users_transactions:
            expenses_to_create.append(Expense(
                user=user,
                amount=users_transaction['amount'] / 100.0,
                cash_type=CashType.objects.get(name='UAH'),
                timestamp=users_transaction['time'],
                description=users_transaction['description'],
                expense_type=MMC.get(str(users_transaction['mcc']))
            ))
            log.info(f"Expenses to create: {expenses_to_create}")

    if expenses_to_create:
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
        The timestamp of the latest expense as a datetime object, or None if there are no expenses.
    """
    latest_expense = Expense.objects.order_by('-timestamp').first()
    return latest_expense.timestamp if latest_expense else None



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
    latest_timestamp = get_latest_expense_timestamp()
    current_time = int(datetime.now().timestamp())
    if latest_timestamp is None:
        return get_current_month_time_bounds()
    return int(latest_timestamp.replace(tzinfo=timezone.utc).timestamp()), current_time



def load_expenses_from_files(user):
    """
    Load expenses from JSON files and save them to the database for the given user.
    """
    data_directory = os.path.join(settings.BASE_DIR, 'data', 'statements', user.username)
    cash_type = CashType.objects.get(name='UAH')
    expenses_to_create = []

    for root, dirs, files in os.walk(data_directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    transactions = json.load(f)
                    for transaction in transactions:
                        amount = transaction['amount'] / 100.0
                        if amount < 0:  # Exclude positive transactions
                            expenses_to_create.append(Expense(
                                user=user,
                                amount=abs(amount),  # Take the absolute value of negative amounts
                                cash_type=cash_type,
                                timestamp=transaction['time'],
                                description=transaction['description'],
                                expense_type=settings.MMC.get(str(transaction['mcc']), 'Unknown')
                            ))

    if expenses_to_create:
        Expense.objects.bulk_create(expenses_to_create)


def generate_pdf_report(user, expenses, expense_summary, period):
    filename = f"{user.username}_expense_report_{period}.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Register the DejaVu Sans font
    pdfmetrics.registerFont(TTFont('roboto', 'data/roboto.ttf'))
    c.setFont("roboto", 16)
    c.drawString(100, height - 50, f"Expense Report for {user.username}")

    c.setFont("roboto", 12)
    c.drawString(100, height - 80, f"Period: {period.capitalize()}")

    c.drawString(100, height - 110, "Expenses by Category:")

    table_data = [["Category", "Amount"]]
    for category, amount in expense_summary.items():
        table_data.append([category, f"{amount:.2f}"])

    c.setFont("roboto", 10)
    x_offset = 140
    y_offset = height - 140
    line_height = 17

    for row in table_data:
        c.drawString(x_offset, y_offset, row[0])
        c.drawRightString(x_offset + 250, y_offset, row[1])
        y_offset -= line_height
        c.line(x_offset, y_offset, x_offset + 250, y_offset)

    c.save()
    return filename
