# Use prebuilt PyTorch CPU image
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

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

# Pre-download transformer model to /app/model_cache
RUN python -c "from transformers import AutoTokenizer, AutoModel; \
    AutoTokenizer.from_pretrained('nlpaueb/legal-bert-base-uncased', cache_dir='/app/model_cache'); \
    AutoModel.from_pretrained('nlpaueb/legal-bert-base-uncased', cache_dir='/app/model_cache')"

# Copy application code
COPY . .

# Expose port
EXPOSE 8001

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
