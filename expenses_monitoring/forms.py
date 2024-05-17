from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import BankConnection, Consultation, Goal


class RegisterForm(UserCreationForm):

    class Meta:
        model = get_user_model()  # Automatically fetches the custom user model
        fields = ['username', 'email', 'password1', 'password2']


class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=150)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())


class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = BankConnection
        fields = ['api_key']
        labels = {
            'api_key': 'Введіть ключ',
        }
        widgets = {
            'api_key': forms.PasswordInput(attrs={'placeholder': '**********'}),
        }


class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['description', 'amount', 'cash_type', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'placeholder': 'Введіть суму'}),
            'description': forms.TextInput(attrs={'placeholder': 'Введіть ціль'}),
            'cash_type': forms.Select()
        }
        labels = {
            'description': 'Введіть ціль',
            'amount': 'Введіть бажану суму для досягнення цілі',
            'cash_type': 'Виберіть тип коштів',
            'date': 'Виберіть дату'
        }

class BankConnectionForm(forms.ModelForm):
    class Meta:
        model = BankConnection
        fields = '__all__'
        widgets = {
            'api_key': forms.PasswordInput(render_value=True),
        }

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['approved']
