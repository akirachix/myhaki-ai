# Use standard Python image (lazy-load models)
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TRANSFORMERS_CACHE=/app/model_cache

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the dynamic port (Cloud Run sets $PORT)
EXPOSE $PORT

# Start FastAPI using the Cloud Run assigned port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
