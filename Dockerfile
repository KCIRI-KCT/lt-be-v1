FROM python:3.12-slim

# Prevent Python from writing .pyc files & buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for PostgreSQL & build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Expose backend port 8000
EXPOSE 8000

# Start script: Run migrations, seed baseline data, and start Gunicorn WSGI server
CMD ["sh", "-c", "python manage.py migrate --fake-initial --noinput && python manage.py seed_data && gunicorn --bind 0.0.0.0:8000 --workers 3 lt_be_v1.wsgi:application"]
