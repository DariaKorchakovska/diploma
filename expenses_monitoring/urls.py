from django.urls import path
from .views import (
    index,
    login,
    add_api_key,
    request_consultation,
    create_goal,
    expense_analysis,
    register,
    filter_expenses,
    consultation_list,
    generate_pdf_report_view,
)
from django.contrib.auth import views as auth_views


urlpatterns = [
    path("", index, name="index"),
    path("register", register, name="register"),
    path("login/", login, name="login"),
    path("add-api-key/", add_api_key, name="add_api_key"),
    path("request-consultation/", request_consultation, name="request_consultation"),
    path("create-goal/", create_goal, name="create_goal"),
    path("expense-analysis/", expense_analysis, name="expense_analysis"),
    path("filter-expenses/", filter_expenses, name="filter_expenses"),
    path("generate-pdf-report/", generate_pdf_report_view, name="generate_pdf_report"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("consultations/", consultation_list, name="consultation_list"),
    # Add other paths
]
