# Description: This file contains the views for the expenses_monitoring app.
import logging
import threading

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from .forms import RegisterForm, LoginForm, ApiKeyForm, ConsultationForm, GoalForm, ConsultationAPPForm
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test

from .lib import sync_user_accounts, get_previous_month_time_bounds, get_latest_bounds, \
    load_expenses_from_files, generate_pdf_report, fetch_and_update_expenses
from .models import Goal, Consultation, Expense
import os
from django.http import FileResponse

log = logging.getLogger(__name__)


def index(request):
    if request.user.is_authenticated:
        # Fetch the user's financial goals and consultations
        goals = Goal.objects.filter(user=request.user)
        consultations = Consultation.objects.filter(user=request.user)
        # Pass these to the template
        return render(request, 'index.html', {'goals': goals, 'consultations': consultations})
    # If the user is not authenticated, just render the basic index page
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        log.info(f"new user registration form submitted.")
        log.info(f"form data: {form.data}")
        if form.is_valid():
            user = form.save()
            log.info(f"new useer {user.username} created.")
            auth_login(request, user)  # Log the user in directly after registration

            return redirect('index')  # Redirect to a home page or other appropriate page
        else:
            return render(request, 'register.html', {'form': form})
    else:
        form = RegisterForm()
        return render(request, 'register.html', {'form': form})


def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            log.info(f"User {username} attempted to log in.")
            if user is not None:
                auth_login(request, user)
                log.info(f"User {user.username}{request.user} logged in.")
                return redirect('index')  # Redirect to a home page or dashboard
            else:
                return render(request, 'login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
        return render(request, 'login.html', {'form': form})


@login_required
def add_api_key(request):
    """
    Add API key for the user
    """

    log.info(f"User {request.user} requested to add API key.")

    if request.method == 'POST':
        if request.user.api_key:
            return redirect('index')
        form = ApiKeyForm(request.POST)
        if request.user.api_key:
            return redirect('add_api_key')
        if form.is_valid():
            api_key_instance = form.save(commit=False)
            api_key_instance.user = request.user
            api_key_instance.save()
            log.info(f"API key {api_key_instance.api_key} added for user {request.user}")
            api_key = request.user.api_key
            if api_key:
                sync_user_accounts(request.user)
            start_of_previous_month, end_of_previous_month = get_previous_month_time_bounds()
            threadm = threading.Thread(target=sync_user_accounts,
                                       args=(request.user, start_of_previous_month, end_of_previous_month))
            threadm.start()
            return redirect('index')
    else:
        form = ApiKeyForm()
    return render(request, 'add_api_key.html', {'form': form})


@login_required
def request_consultation(request):
    """
    Request a consultation
    """
    if request.method == 'POST':
        form = ConsultationForm(request.POST)
        if form.is_valid():
            consultation = form.save(commit=False)
            consultation.user = request.user
            consultation.approved = False  # Ставимо за замовчуванням, що не затверджено
            consultation.save()
            return redirect('index')  # Перенаправляємо на головну сторінку або на сторінку успіху
    else:
        form = ConsultationForm()
    return render(request, 'request_consultation.html', {'form': form})


@login_required
def create_goal(request):
    if request.method == 'POST':
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('index')
    else:
        form = GoalForm()
    return render(request, 'create_goal.html', {'form': form})



@login_required
def filter_expenses(request):
    user = request.user
    period = request.GET.get('period')

    now = datetime.now()
    if period == 'week':
        start_date = now - timedelta(days=now.weekday())
        start_date_last_year = start_date - timedelta(weeks=52)
        end_date_last_year = now - timedelta(weeks=52)
    elif period == 'month':
        start_date = datetime(now.year, now.month, 1)
        start_date_last_year = datetime(now.year - 1, now.month, 1)
        end_date_last_year = start_date_last_year + timedelta(days=31)
        end_date_last_year = end_date_last_year.replace(day=1) - timedelta(seconds=1)
    elif period == 'year':
        start_date = datetime(now.year, 1, 1)
        start_date_last_year = datetime(now.year - 1, 1, 1)
        end_date_last_year = datetime(now.year - 1, 12, 31)
    else:
        start_date = now - timedelta(days=7)
        start_date_last_year = start_date - timedelta(weeks=52)
        end_date_last_year = now - timedelta(weeks=52)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(now.timestamp())
    start_timestamp_last_year = int(start_date_last_year.timestamp())
    end_timestamp_last_year = int(end_date_last_year.timestamp())

    expenses = Expense.objects.filter(user=user, timestamp__gte=start_timestamp, timestamp__lte=end_timestamp)
    expenses_last_year = Expense.objects.filter(user=user, timestamp__gte=start_timestamp_last_year, timestamp__lte=end_timestamp_last_year)

    expense_summary = {}
    expense_summary_last_year = {}

    for expense in expenses:
        if expense.expense_type not in expense_summary:
            expense_summary[expense.expense_type] = 0
        expense_summary[expense.expense_type] += expense.amount

    for expense in expenses_last_year:
        if expense.expense_type not in expense_summary_last_year:
            expense_summary_last_year[expense.expense_type] = 0
        expense_summary_last_year[expense.expense_type] += expense.amount

    pdf_url = f"/generate-pdf-report/?period={period}"

    return JsonResponse({
        'expense_summary': expense_summary,
        'expense_summary_last_year': expense_summary_last_year,
        'pdf_url': pdf_url
    })


@login_required
def expense_analysis(request):
    user = request.user
    if Expense.objects.filter(user=user).count() == 0:
        load_expenses_from_files(user)
    else:
        start_of_current_month, current_time = get_latest_bounds()
        thread = threading.Thread(target=fetch_and_update_expenses, args=(user, start_of_current_month, current_time))
        thread.start()

    return render(request, 'expense_analysis.html')


def is_staff(user):
    return user.is_staff


@user_passes_test(is_staff)
def consultation_list(request):
    consultations = Consultation.objects.filter(approved=False)
    if request.method == 'POST':
        consultation_id = request.POST.get('consultation_id')
        consultation = Consultation.objects.get(id=consultation_id)
        approved = request.POST.get(f'approved_{consultation_id}') == 'on'
        consultation.approved = approved
        consultation.save()
        return redirect('consultation_list')

    context = {
        'consultations': consultations,
    }
    return render(request, 'consultation_list.html', context)



@login_required
def generate_pdf_report_view(request):
    user = request.user
    period = request.GET.get('period')

    now = datetime.now()
    if period == 'week':
        start_date = now - timedelta(days=now.weekday())
    elif period == 'month':
        start_date = datetime(now.year, now.month, 1)
    elif period == 'year':
        start_date = datetime(now.year, 1, 1)
    else:
        start_date = now - timedelta(days=7)

    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(now.timestamp())

    expenses = Expense.objects.filter(user=user, timestamp__gte=start_timestamp, timestamp__lte=end_timestamp)

    expense_summary = {}
    for expense in expenses:
        if expense.expense_type not in expense_summary:
            expense_summary[expense.expense_type] = 0
        expense_summary[expense.expense_type] += expense.amount

    filename = generate_pdf_report(user, expenses, expense_summary, period)
    response = FileResponse(open(filename, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'

    return response
