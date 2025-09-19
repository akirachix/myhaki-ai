# Use standard Python image (no prebuilt PyTorch image, lazy-load instead)
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    TRANSFORMERS_CACHE=/app/model_cache

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Pre-download transformer model to cache (optional, can lazy-load instead)
# If you want lazy-loading, comment this block out
# RUN python -c "from transformers import AutoTokenizer, AutoModel; \
#     AutoTokenizer.from_pretrained('nlpaueb/legal-bert-base-uncased', cache_dir='/app/model_cache'); \
#     AutoModel.from_pretrained('nlpaueb/legal-bert-base-uncased', cache_dir='/app/model_cache')"

# Copy app code
COPY . .

# Expose the port (optional, Cloud Run uses $PORT)
EXPOSE $PORT

# Start FastAPI using Cloud Run dynamic port
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
