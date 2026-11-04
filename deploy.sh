#!/bin/bash
# ==============================================================================
# Lumina AI Background Remover — Production Deployment Script (Linux / Ubuntu)
# ==============================================================================

set -e

echo "=============================================================================="
echo "      Deploying Lumina AI Background Remover to Production"
echo "=============================================================================="

# 1. Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "[ERROR] Docker is not installed. Please install Docker first."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { echo "[ERROR] Docker Compose is not installed."; exit 1; }

# 2. Environment file validation
if [ ! -f .env ]; then
    echo "[INFO] .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "[ACTION REQUIRED] Please edit .env with your domain name and production passwords before proceeding!"
fi

# 3. Pull latest base images and build containers
echo "[1/4] Building production Docker containers..."
docker compose build --pull

# 4. Run database migrations
echo "[2/4] Initializing database and storage..."
docker compose up -d db
echo "Waiting for PostgreSQL database container to become healthy..."
docker compose exec -T db sh -c 'until pg_isready -U postgres; do sleep 1; done'

# 5. Launch all services
echo "[3/4] Starting web application and reverse proxy services..."
docker compose up -d

# 6. Verify health check
echo "[4/4] Verifying production health check..."
sleep 5
curl -f http://localhost:5000/api/health || { echo "[WARNING] Health check pending or degraded. Inspect logs with: docker compose logs -f"; }

echo ""
echo "=============================================================================="
echo "  ✓ Lumina AI is now running in production!"
echo "  View live logs: docker compose logs -f web"
echo "  Stop services:  docker compose down"
echo "=============================================================================="
