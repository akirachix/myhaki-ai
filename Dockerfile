# Base image
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8001 \
    TRANSFORMERS_CACHE=/app/model_cache

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose FastAPI port
EXPOSE 8001

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
