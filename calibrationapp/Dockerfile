FROM python:3.13-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=calibrationapi.settings

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

RUN python manage.py collectstatic --noinput
# Expose application port
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "calibrationapi.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--workers", "2", "--timeout", "60"]