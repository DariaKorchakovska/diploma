from django.contrib import admin

from .models import BankConnection, Consultation, Goal, CustomUser, CashType, Expense, Account


class BankConnectionAdmin(admin.ModelAdmin):
    list_display = ['user', 'api_key']
    list_filter = ['user']


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'time', 'approved']
    list_filter = ['user', 'approved']


class GoalAdmin(admin.ModelAdmin):
    list_display = ['user', 'description', 'amount', 'cash_type', 'date']
    list_filter = ['user', 'cash_type']


admin.site.register(BankConnection, BankConnectionAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Goal, GoalAdmin)
admin.site.register(CustomUser)
admin.site.register(CashType)
admin.site.register(Expense)
admin.site.register(Account)
