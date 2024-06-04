from datetime import datetime

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Custom user model with additional fields.
    """

    @property
    def api_key(self):
        return self.bankconnection.first().api_key if self.bankconnection.exists() else None

    @property
    def accounts(self):
        return [account.account_id for account in Account.objects.filter(user=self)]

    def __str__(self):
        return self.username


class CashType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        indexes = [
            models.Index(fields=["name"]),  # Index on name for filtering by name
        ]


class Goal(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField()
    amount = models.FloatField()
    cash_type = models.ForeignKey(CashType, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["user"]),  # Single index on user if filtering by user alone is common
        ]


class BankConnection(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="bankconnection")
    api_key = models.CharField(max_length=100)

    class Meta:
        unique_together = ["user", "api_key"]


class Account(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    account_id = models.CharField(max_length=25)
    maskedPan = models.CharField(max_length=25)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),  # Single index on user if filtering by user alone is common
        ]

    def __str__(self):
        return f"Account: {self.maskedPan} - {self.user}"


class Expense(models.Model):
    user = models.ForeignKey(
        "CustomUser", on_delete=models.CASCADE
    )  # Assuming 'CustomUser' is correctly defined elsewhere
    amount = models.FloatField()
    cash_type = models.ForeignKey("CashType", on_delete=models.CASCADE)
    timestamp = models.BigIntegerField(default=int(datetime.now().timestamp()))
    description = models.TextField()
    expense_type = models.CharField(max_length=100)

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),  # Corrected from 'date' to 'timestamp'
            models.Index(fields=["user"]),
            models.Index(fields=["expense_type"]),
        ]

    @property
    def readable_date(self):
        """Return a formatted datetime string from the timestamp."""
        return datetime.utcfromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def __str__(self):
        return (
            f"Expense: {self.amount} {self.cash_type} - {self.readable_date} "
            f"- {self.expense_type} - {self.description} - {self.user}"
        )


class Consultation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    approved = models.BooleanField()

    class Meta:
        indexes = [
            models.Index(fields=["date"]),  # Index on date for filtering or sorting by date
            models.Index(fields=["user"]),  # Single index on user if filtering by user alone is common
        ]

    def __str__(self):
        return f"Consultation: {self.user} - {self.date} - {self.time} - {self.approved}"
