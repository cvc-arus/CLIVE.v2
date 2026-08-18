#!/bin/bash
# CLIVE Phase 2 - Service Health Verification
# Run this after docker compose up to confirm all services are operational.

set -e

echo "=== CLIVE Phase 2 - Service Verification ==="
echo ""

# Check Docker containers are running
echo "[1/5] Checking container status..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(clive-)" || {
    echo "ERROR: Containers not found. Run 'docker compose up -d' first."
    exit 1
}
echo ""

# Check PostgreSQL with PGVector
echo "[2/5] Checking PostgreSQL + PGVector..."
docker exec clive-postgres psql -U clive -d clive -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';" 2>/dev/null || {
    echo "ERROR: PGVector extension not available."
    exit 1
}
echo ""

# Check Apache Tika
echo "[3/5] Checking Apache Tika..."
TIKA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9998/tika)
if [ "$TIKA_STATUS" = "200" ]; then
    echo "Tika is responding (HTTP 200)"
else
    echo "ERROR: Tika not responding (HTTP $TIKA_STATUS)"
    exit 1
fi
echo ""

# Check Ollama
echo "[4/5] Checking Ollama..."
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
echo "[5/5] Checking Open WebUI..."
WEBUI_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$WEBUI_STATUS" = "200" ] || [ "$WEBUI_STATUS" = "302" ]; then
    echo "Open WebUI is responding (HTTP $WEBUI_STATUS)"
else
    echo "ERROR: Open WebUI not responding (HTTP $WEBUI_STATUS)"
    exit 1
fi
echo ""

echo "=== All services verified successfully ==="
echo ""
echo "Access Open WebUI at: http://localhost:3000"
echo "Qdrant Dashboard at: N/A (using PGVector)"
echo "Tika endpoint at:    http://localhost:9998"