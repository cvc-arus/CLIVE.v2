#!/bin/bash
# CLIVE Phases 1-3 - Service Health Verification
# Run this after docker compose up to confirm all services are operational.

set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../.env"

echo "=== CLIVE Phases 1-3 - Service Verification ==="
echo ""

# Check Docker containers are running
echo "[1/7] Checking container status..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(clive-)" || {
    echo "ERROR: Containers not found. Run 'docker compose up -d' first."
    exit 1
}
echo ""

# Check PostgreSQL with PGVector
echo "[2/7] Checking PostgreSQL + PGVector..."
docker exec clive-postgres psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>/dev/null || {
    echo "ERROR: PGVector extension not available."
    exit 1
}
echo ""

# Check Apache Tika
echo "[3/7] Checking Apache Tika..."
TIKA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9998/tika)
if [ "$TIKA_STATUS" = "200" ]; then
    echo "Tika is responding (HTTP 200)"
else
    echo "ERROR: Tika not responding (HTTP $TIKA_STATUS)"
    exit 1
fi
echo ""

# Check Ollama
echo "[4/7] Checking Ollama..."
OLLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:11435/api/tags)
if [ "$OLLAMA_STATUS" = "200" ]; then
    echo "Ollama is responding (HTTP 200)"
    # Check for nomic-embed-text
    if curl -s http://localhost:11435/api/tags | grep -q "nomic-embed-text"; then
        echo "nomic-embed-text model is available"
    else
        echo "WARNING: nomic-embed-text not pulled yet. Run: ollama pull nomic-embed-text"
    fi
else
    echo "ERROR: Ollama not responding (HTTP $OLLAMA_STATUS)"
    exit 1
fi
echo ""

# Check Open WebUI
echo "[5/7] Checking Open WebUI..."
WEBUI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$WEBUI_STATUS" = "200" ] || [ "$WEBUI_STATUS" = "302" ]; then
    echo "Open WebUI is responding (HTTP $WEBUI_STATUS)"
else
    echo "ERROR: Open WebUI not responding (HTTP $WEBUI_STATUS)"
    exit 1
fi
echo ""

# Check Simpro mock database (uses the container's own POSTGRES_USER/POSTGRES_DB)
echo "[6/7] Checking Simpro mock database..."
docker exec clive-simpro-mock-db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' || {
    echo "ERROR: Simpro mock database not ready."
    exit 1
}
echo ""

# Check Simpro mock API
echo "[7/7] Checking Simpro mock API..."
MOCK_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8100/health)
if [ "$MOCK_STATUS" = "200" ]; then
    echo "Simpro mock is responding (HTTP 200)"
else
    echo "ERROR: Simpro mock not responding (HTTP $MOCK_STATUS)"
    exit 1
fi
echo ""

echo "=== All services verified successfully ==="
echo ""
echo "Access Open WebUI at: http://localhost:3000"
echo "Qdrant Dashboard at: N/A (using PGVector)"
echo "Tika endpoint at:    http://localhost:9998"