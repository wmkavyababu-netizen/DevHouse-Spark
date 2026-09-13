# Dockerfile for TARANG FastAPI Application & Pipeline Engine
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies for GIS, OpenCV, and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend-app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and Alembic migrations
COPY backend-app/alembic.ini .
COPY backend-app/alembic ./alembic
COPY backend-app/app ./app

# Create storage directory inside container
RUN mkdir -p /app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
