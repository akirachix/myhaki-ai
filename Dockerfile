# Use prebuilt PyTorch CPU image (includes torch)
FROM pytorch/pytorch:2.1.0-cpu

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8001 \
    TRANSFORMERS_CACHE=/app/model_cache

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements (without torch)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy your FastAPI app and RAG code
COPY . .

# Create model cache directory (used for lazy-loading)
RUN mkdir -p /app/model_cache

# Expose port
EXPOSE 8001

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
