"""
URL configuration for exp_d project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from expenses_monitoring.views import login, register

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("expenses_monitoring.urls")),
    path(
        "accounts/",
        # include('allauth.urls'),
        include(
            [
                path("login/", login, name="login"),
                path(
                    "logout/",
                    auth_views.LogoutView.as_view(next_page="index"),
                    name="logout",
                ),
                path("register/", register, name="register"),
                path(
                    "password_reset/",
                    auth_views.PasswordResetView.as_view(),
                    name="password_reset",
                ),
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
                # Добавьте остальные URL-пути, перечисленные в вашем вопросе
            ]
        ),
    ),
]
