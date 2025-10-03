# Backend Dockerfile
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install torch==2.8.0 && \
    pip install -r requirements.txt
# Copy project files
COPY . .

# Static files will be collected after container is running

# Run Gunicorn as WSGI server
CMD ["gunicorn", "op_mental.wsgi:application", "--bind", "0.0.0.0:8000", "--workers=4"]
