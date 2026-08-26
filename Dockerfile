#FROM python:3.12-slim
#
## Prevent Python from writing .pyc files & buffer stdout/stderr
#ENV PYTHONDONTWRITEBYTECODE=1
#ENV PYTHONUNBUFFERED=1
#
#WORKDIR /app
#
## Install system dependencies required for PostgreSQL & build tools
#RUN apt-get update && apt-get install -y --no-install-recommends \
#    gcc \
#    libpq-dev \
#    && rm -rf /var/lib/apt/lists/*
#
## Install Python requirements
#COPY requirements.txt /app/
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy application source code
#COPY . /app/
#
## Expose backend port 8000
#EXPOSE 8000
#
## Start script: Run migrations, seed baseline data, and start Daphne ASGI server
#CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_data && daphne -b 0.0.0.0 -p 8000 core.asgi:application"]
#
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PostgreSQL compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir daphne channels-redis

COPY . .

EXPOSE 8000

# Run Daphne ASGI server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "lt_be_v1.asgi:application"]