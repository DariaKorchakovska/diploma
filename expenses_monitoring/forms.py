from datetime import datetime, date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinLengthValidator,
    MaxLengthValidator,
    EmailValidator,
)

from .models import BankConnection, Consultation, Goal


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        validators=[
            EmailValidator(message="Введите правильный адрес электронной почты.")
        ],
    )

    password1 = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput,
        validators=[
            MinLengthValidator(8, message="Пароль должен быть не менее 8 символов."),
            MaxLengthValidator(50, message="Пароль должен быть не более 50 символов."),
        ],
    )

    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Введите пароль ещё раз для подтверждения.",
        validators=[
            MinLengthValidator(8, message="Пароль должен быть не менее 8 символов."),
            MaxLengthValidator(50, message="Пароль должен быть не более 50 символов."),
        ],
    )

    class Meta:
        model = get_user_model()  # Automatically fetches the custom user model
        fields = ["username", "email", "password1", "password2"]


class LoginForm(forms.Form):
    username = forms.CharField(label="Username", max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput())


class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = BankConnection
        fields = ["api_key"]
        labels = {
            "api_key": "Введіть ключ",
        }
        widgets = {
            "api_key": forms.PasswordInput(attrs={"placeholder": "**********"}),
        }


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ["date", "time"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        time = cleaned_data.get("time")

        if date and time:
            consultation_datetime = datetime.combine(date, time)
            if consultation_datetime < datetime.now():
                raise ValidationError(
                    "Неможливо замовити консультацію на минулі дати або години."
                )

        return cleaned_data


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["description", "amount", "cash_type", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"placeholder": "Введіть суму"}),
            "description": forms.TextInput(attrs={"placeholder": "Введіть ціль"}),
            "cash_type": forms.Select(),
        }
        labels = {
            "description": "Введіть ціль",
            "amount": "Введіть бажану суму для досягнення цілі",
            "cash_type": "Виберіть тип коштів",
            "date": "Виберіть дату",
        }

    def clean_date(self):
        selected_date = self.cleaned_data["date"]
        if selected_date < date.today():
            raise ValidationError("Неможливо встановити ціль на минулу дату.")
        return selected_date


class BankConnectionForm(forms.ModelForm):
    api_key = forms.CharField(
        widget=forms.PasswordInput(render_value=True),
        validators=[MinLengthValidator(32), MaxLengthValidator(128)],
    )

    class Meta:
        model = BankConnection
        fields = "__all__"


class ConsultationAPPForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ["approved"]
