#!/bin/bash
# ==============================================================================
# Lumina AI Background Remover — Production Deployment Script
# Domain: www.parasnathpokharel.com.np
# ==============================================================================

set -e

DOMAIN="parasnathpokharel.com.np"
WWW_DOMAIN="www.parasnathpokharel.com.np"

echo "=============================================================================="
echo "   Deploying Lumina AI Background Remover"
echo "   Target Domain : https://$WWW_DOMAIN"
echo "=============================================================================="

# 1. Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "[ERROR] Docker is not installed. Install via: curl -fsSL https://get.docker.com | sh"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1 || { echo "[ERROR] Docker Compose not found. Install Docker Desktop or docker-compose-plugin."; exit 1; }

# 2. Environment file validation
if [ ! -f .env ]; then
    echo "[INFO] .env not found — creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "  [ACTION REQUIRED] Edit .env before continuing:"
    echo "    - Set SECRET_KEY to a randomly generated 32-byte hex string"
    echo "    - Set POSTGRES_PASSWORD to a secure database password"
    echo "    - Set LETSENCRYPT_EMAIL to your real email address"
    echo ""
    read -p "  Press ENTER once you have saved .env to continue deployment..."
fi

# 3. Build production containers
echo ""
echo "[1/5] Building production Docker containers..."
docker compose build --pull

# 4. Start database, wait for health
echo "[2/5] Starting PostgreSQL database container..."
docker compose up -d db
echo "  Waiting for PostgreSQL to become healthy..."
for i in $(seq 1 30); do
    if docker compose exec -T db pg_isready -U postgres >/dev/null 2>&1; then
        echo "  PostgreSQL is ready."
        break
    fi
    sleep 2
done

# 5. Run database schema migrations inside the web container
echo "[3/5] Running database schema migrations..."
docker compose run --rm web python backend/migrations.py

# 6. Launch all services (web + caddy SSL proxy)
echo "[4/5] Starting web application and Caddy SSL reverse proxy..."
docker compose up -d

# 7. Verify health check
echo "[5/5] Verifying backend health check..."
sleep 6
if curl -sf http://localhost:5000/api/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('  Model:', d['model_loaded'], '| DB:', d['database_connected'])" 2>/dev/null; then
    echo "  Backend health check passed."
else
    echo "  [WARNING] Health check pending — the AI model may still be loading."
    echo "  Run 'docker compose logs -f web' to monitor startup."
fi

echo ""
echo "=============================================================================="
echo "  Lumina AI is live!"
echo ""
echo "  Production URL : https://$WWW_DOMAIN"
echo "  API Health     : https://$WWW_DOMAIN/api/health"
echo ""
echo "  Useful commands:"
echo "    View logs        : docker compose logs -f web"
echo "    View all logs    : docker compose logs -f"
echo "    Stop everything  : docker compose down"
echo "    Restart web only : docker compose restart web"
echo "    DB backup        : docker compose exec web python backend/backup.py"
echo "=============================================================================="
