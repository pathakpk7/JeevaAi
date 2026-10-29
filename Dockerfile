# PRODUCTION DOCKERFILE FOR MEDICAL KNOWLEDGE ASSISTANT
FROM python:3.13-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
# Restrict OpenMP and MKL thread pools to avoid excessive RAM usage in 512MB environments
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    DEBUG=false \
    PORT=5000 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download SentenceTransformer embedding model for instant startup without runtime download delays
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application source code and assets
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY data/ ./data/
COPY vectorstore/ ./vectorstore/

# Expose default port
EXPOSE 5000

# Healthcheck probe using dynamic PORT environment variable
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/api/health || exit 1

# Launch using Gunicorn with 1 worker and 2 threads (optimized for memory efficiency on Render/Railway 512MB RAM)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 2 --timeout 180 'app:create_app()'"]
