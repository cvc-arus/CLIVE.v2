#!/bin/bash
# CLIVE Phase 2 - PGVector Backup Script
# Performs a full pg_dump of the vector database with verification and rotation.

set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../.env"

BACKUP_DIR="${BACKUP_DIR:-${SCRIPT_DIR}/../backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/clive_pgvector_${TIMESTAMP}.sql.gz"

echo "=== CLIVE PGVector Backup ==="
echo "Timestamp: ${TIMESTAMP}"
echo "Backup dir: ${BACKUP_DIR}"
echo ""

# Create backup directory if it does not exist
mkdir -p "${BACKUP_DIR}"

# Perform the backup
echo "[1/4] Running pg_dump..."
docker exec clive-postgres pg_dump -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" | gzip > "${BACKUP_FILE}"
echo "Backup saved to: ${BACKUP_FILE}"
echo ""

# Verify backup integrity
echo "[2/4] Verifying backup integrity..."
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "ERROR: Backup file does not exist."
    exit 1
fi

FILESIZE=$(stat -c%s "${BACKUP_FILE}")
if [ "${FILESIZE}" -eq 0 ]; then
    echo "ERROR: Backup file is empty."
    exit 1
fi
echo "File size: ${FILESIZE} bytes"

# Check backup contains pgvector extension reference
if zcat "${BACKUP_FILE}" | grep -q "vector"; then
    echo "Backup contains vector extension reference."
else
    echo "WARNING: Backup may not contain pgvector data."
fi
echo ""


# Restore verification (to a temporary database)
echo "[3/4] Running restore verification..."
docker exec clive-postgres psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS clive_backup_test;" 2>/dev/null
docker exec clive-postgres psql -U "${POSTGRES_USER}" -c "CREATE DATABASE clive_backup_test;"
zcat "${BACKUP_FILE}" | docker exec -i clive-postgres psql -U "${POSTGRES_USER}" -d clive_backup_test > /dev/null 2>&1

# Verify the restored database has the vector extension
VECTOR_CHECK=$(docker exec clive-postgres psql -U "${POSTGRES_USER}" -d clive_backup_test -t -c "SELECT count(*) FROM pg_extension WHERE extname = 'vector';")
if [ "$(echo "${VECTOR_CHECK}" | tr -d ' ')" = "1" ]; then
    echo "Restore verification PASSED: vector extension present."
else
    echo "ERROR: Restore verification FAILED: vector extension missing."
    docker exec clive-postgres psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS clive_backup_test;" 2>/dev/null
    exit 1
fi

# Clean up test database
docker exec clive-postgres psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS clive_backup_test;" 2>/dev/null
echo ""

# Rotate old backups
echo "[4/4] Rotating old backups (keeping last ${RETENTION_DAYS} days)..."
DELETED=$(find "${BACKUP_DIR}" -name "clive_pgvector_*.sql.gz" -mtime +${RETENTION_DAYS} -print -delete | wc -l)
echo "Deleted ${DELETED} old backup(s)."
echo ""

echo "=== Backup complete and verified ==="
echo "File: ${BACKUP_FILE}"
echo "Size: $(du -h "${BACKUP_FILE}" | cut -f1)"