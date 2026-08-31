# PRODUCTION DOCKERFILE FOR MEDICAL KNOWLEDGE ASSISTANT
FROM python:3.13-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_ENV=production \
    DEBUG=false \
    PORT=5000

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

# Copy application source code and assets
COPY app.py .
COPY src/ ./src/
COPY templates/ ./templates/
COPY static/ ./static/
COPY data/ ./data/

# Expose port
EXPOSE 5000

# Healthcheck probe using health API endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Launch using Gunicorn production WSGI server calling the canonical app factory
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "120", "app:create_app()"]
