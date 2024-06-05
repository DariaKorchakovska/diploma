# Django Expense Monitoring Project

Цей проект на Django призначений для моніторингу витрат користувачів, включає функціонал для додавання API ключів,
встановлення цілей, аналізу витрат та реєстрації користувачів.

## Вміст проекту

- `models.py`: Моделі бази даних.
- `forms.py`: Форми для введення даних.
- `views.py`: Представлення для обробки запитів.
- `urls.py`: Маршрутизація запитів.
- `docker-compose.yaml`: Налаштування Docker Compose.
- `Dockerfile`: Файл для створення Docker образу.

## Встановлення та запуск проекту

### Кроки для запуску за допомогою Docker Compose

1. Клонуйте репозиторій:
    ```sh
    git clone https://github.com/DariaKorchakovska/diploma.git
    cd diploma
    ```

2. Запустіть Docker Compose:
    ```sh
    docker-compose up --build
    ```
   або
    ```sh
    docker-compose up --build -d
    ```
   для запуску в фоновому режимі.

### Docker Compose Налаштування

Файл `docker-compose.yaml` містить налаштування для запуску проекту в контейнері Docker:

```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: django_app # Назва контейнера
    ports: # Порти для доступу до сервера
      - "8000:8000"
    volumes:
      - ./data:/app/data # Папка для зберігання бази даних
      - ./staticfiles:/app/staticfiles # Папка для зберігання статичних файлів
      - ./static:/app/static # Папка для зберігання статичних файлів
      - ./expenses_monitoring/migrations:/app/expenses_monitoring/migrations # Папка для зберігання міграцій
    command: gunicorn --log-level info --workers 3 --timeout 1200 --bind :8000 exp_d.wsgi:application # Команда для запуску сервера

volumes:
  app:
  data:
  staticfiles:
```

### Dockerfile Налаштування

Файл `Dockerfile` містить інструкції для створення Docker образу:

```Dockerfile
# базовий образ
FROM python:3.9

# Встановіть залежності
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Скопіюйте проект у робочу директорію
COPY . /app/

# Виконайте команди для збору статичних файлів та міграції бази даних
RUN python manage.py collectstatic --noinput
RUN python manage.py migrate

# Вкажіть команду для запуску сервера
CMD ["gunicorn", "--log-level", "info", "--workers", "3", "--timeout", "1200", "--bind", ":8000", "exp_d.wsgi:application"]
```

## Моделі бази даних

### CustomUser

Модель користувача, яка розширює стандартну модель користувача Django

```python
class CustomUser(AbstractUser):
    @property
    def api_key(self):
        return self.bankconnection.first().api_key if self.bankconnection.exists() else None
```

### Expense

Модель витрат, яка містить інформацію про користувача, суму, тип валюти, дату, опис та тип витрати.

```python
class Expense(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    amount = models.FloatField()
    cash_type = models.ForeignKey("CashType", on_delete=models.CASCADE)
    timestamp = models.BigIntegerField(default=int(datetime.now().timestamp()))
    description = models.TextField()
    expense_type = models.CharField(max_length=100)

    def __str__(self):
        return f"Expense: {self.amount} {self.cash_type} - {self.readable_date}"

    @property
    def readable_date(self):
        return datetime.utcfromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
```

### CashType

Модель типу валюти, яка містить інформацію про назву валюти.

```python
class CashType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
```

### Goal

Модель фінансової цілі, яка містить інформацію про користувача, суму, тип валюти, дату та опис.

```python
class Goal(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.PositiveIntegerField()
    cash_type = models.ForeignKey("CashType", on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return f"Goal: {self.description} - {self.amount} {self.cash_type}"
```

### filter_expenses

Це представлення фільтрує витрати користувача за обраним періодом (тиждень, місяць, рік) та порівнює їх з витратами за
аналогічний період попереднього року. Повертає результат у форматі JSON, і використовується длявиводу графіків

```python

@login_required
def filter_expenses(request):
    user = request.user
    period = request.GET.get("period")

    now = datetime.now()
    if period == "week":
        start_date = now - timedelta(days=now.weekday() + 1)
        start_date_last_year = start_date - timedelta(weeks=52)
        end_date_last_year = start_date_last_year + timedelta(days=7)
    elif period == "month":
        start_date = datetime(now.year, now.month, 1) - timedelta(days=1)
        start_date_last_year = datetime(now.year - 1, now.month, 1)
        next_month = start_date_last_year.replace(day=28) + timedelta(days=4)
        end_date_last_year = next_month - timedelta(days=next_month.day)
    elif period == "year":
        start_date = datetime(now.year, 1, 1)
        start_date_last_year = datetime(now.year - 1, 1, 1)
        end_date_last_year = datetime(now.year - 1, 12, 31)
    else:
        start_date = now - timedelta(days=now.weekday() + 1)
        start_date_last_year = start_date - timedelta(weeks=52)
        end_date_last_year = start_date_last_year + timedelta(days=7)

    start_timestamp = int(make_aware(start_date).timestamp())
    end_timestamp = int(make_aware(now).timestamp())
    start_timestamp_last_year = int(make_aware(start_date_last_year).timestamp())
    end_timestamp_last_year = int(make_aware(end_date_last_year).timestamp())

    expenses = Expense.objects.filter(user=user, timestamp__gte=start_timestamp, timestamp__lte=end_timestamp)
    expenses_last_year = Expense.objects.filter(
        user=user,
        timestamp__gte=start_timestamp_last_year,
        timestamp__lte=end_timestamp_last_year,
    )

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

    return JsonResponse(
        {
            "expense_summary": expense_summary,
            "expense_summary_last_year": expense_summary_last_year,
            "pdf_url": pdf_url,
        }
    )
```

## Використання

- Відвідайте
  ` / register / ` для
  реєстрації
  нового
  користувача.
- Відвідайте
  ` / add - api - key / ` для
  додавання
  API
  ключа.
- Відвідайте
  ` / create - goal / ` для
  встановлення
  фінансових
  цілей.
- Відвідайте
  ` / expense - analysis / ` для
  аналізу
  ваших
  витрат.

## CI/CD Налаштування

Файл
`.github / workflows / deploy.yml
` містить
налаштування
для
автоматичного
деплою
на
сервер
при
пуші
до
гілки
`main`.

### Налаштування

```yaml
name: Deploy
  to
  Server

on:
push:
branches:
  - main

jobs:
deploy:
runs - on: ubuntu - latest

steps:
  - name: Checkout
  code
uses: actions / checkout @ v2

  - name: Install
  SSH
  key
uses: webfactory / ssh - agent @ v0
  .5
  .3
with:
  ssh - private - key: ${{secrets.DEPLOY_KEY}}

  - name: Deploy
  to
  Server
env:
HOST: 129.159
  .41
  .235
USER: ubuntu
PORT: 22
run: |
  ssh - o
  StrictHostKeyChecking = no - i
  deploy_key - p $PORT $USER @$HOST / opt / etc / dockers / DariaKorchakovska / diploma / update.sh
```

Це налаштування дозволяє автоматично деплоїти код на сервер, використовуючи SSH ключ, зберігаючи його у секретах GitHub.

