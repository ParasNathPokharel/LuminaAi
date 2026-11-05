# ==============================================================================
# Lumina AI Background Remover — Production Multi-Stage Dockerfile
# ==============================================================================
FROM python:3.11-slim as base

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    STORAGE_DIR=/app/storage \
    U2NET_HOME=/root/.u2net

WORKDIR /app
ENV PYTHONPATH=/app/backend

# Install system dependencies required for OpenCV, Pillow, and C compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Pre-create model directory
RUN mkdir -p /root/.u2net /app/storage /app/uploads /app/outputs

# Copy dependency requirements
COPY requirements.txt /app/

# Install Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source code
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
COPY schema.sql /app/
COPY gunicorn.conf.py /app/

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app /root/.u2net

# Expose HTTP port
EXPOSE 5000

# Health check verifying API & model responsiveness
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Launch startup: execute database migrations then start Gunicorn
CMD ["sh", "-c", "python -m backend.migrations && gunicorn -c gunicorn.conf.py backend.app:app"]
