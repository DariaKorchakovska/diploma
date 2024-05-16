FROM python:3.12-slim
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
COPY . /app/
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "your_project.wsgi:application"]
