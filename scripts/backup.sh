#!/bin/bash
# CLIVE backup script (course correction W5 T3; extends the Phase 2 script).
#
# Backs up everything in the inventory in docs/recovery-plan.md section 7:
#   - Phase 2 Postgres: pg_dump of the knowledge base database plus roles,
#     restore-verified into a temporary database
#   - Open WebUI: online SQLite backup of webui.db, then its other files
#   - the six /data directories no container mounts
#   - .env, encrypted to a GPG public key (skipped with a warning until
#     BACKUP_GPG_RECIPIENT is set)
#   - the Ollama model list and the running image digests
# and writes a SHA-256 MANIFEST.txt, verified before the backup is accepted.
#
# Output: <BACKUP_DIR>/<YYYY-MM-DD_HHMM>/. A run writes to "<name>.partial" and
# renames it only when every step has passed, so a failed run is never mistaken
# for a backup. BACKUP_DIR must be on a different disk from /data.
#
# Settings come from the environment or, failing that, from BACKUP_* lines in
# .env. No other .env value is read: database credentials are taken from the
# containers' own environment.

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_DIR}/.env"

# Load only BACKUP_* settings from .env; values already in the environment win.
# Whitespace (including a CR from Windows line endings) around keys and values
# is stripped, so a stray space cannot change the target or break a number.
if [[ -f "${ENV_FILE}" ]]; then
    while IFS='=' read -r key value; do
        key="${key//[[:space:]]/}"
        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"
        case "${key}" in
            BACKUP_DIR | BACKUP_RETENTION_DAILY | BACKUP_RETENTION_WEEKLY | BACKUP_GPG_RECIPIENT | BACKUP_RETENTION_DAYS)
                if [[ -z "${!key+x}" ]]; then
                    value="${value%\"}"
                    value="${value#\"}"
                    printf -v "${key}" '%s' "${value}"
                fi
                ;;
        esac
    done < <(grep -E '^[[:space:]]*BACKUP_[A-Z_]+[[:space:]]*=' "${ENV_FILE}" || true)
fi

BACKUP_DIR="${BACKUP_DIR:-${HOME}/clive-backups}"
# A relative BACKUP_DIR is taken relative to the repository, not the caller's
# working directory.
[[ "${BACKUP_DIR}" == /* ]] || BACKUP_DIR="${REPO_DIR}/${BACKUP_DIR}"
RETENTION_DAILY="${BACKUP_RETENTION_DAILY:-7}"
RETENTION_WEEKLY="${BACKUP_RETENTION_WEEKLY:-4}"
GPG_RECIPIENT="${BACKUP_GPG_RECIPIENT:-}"

DATA_ROOT="/data"
PG_CONTAINER="clive-postgres"
WEBUI_CONTAINER="clive-webui"
OLLAMA_CONTAINER="clive-ollama"
# Already on the host and includes tar; used to read root-owned directories
# without sudo (docs/recovery-plan.md section 6).
ARCHIVE_IMAGE="postgres:16-alpine"
TEST_DB="clive_backup_test"
WEBUI_TMP="/tmp/clive-webui-backup.db"
# Directories on /data that no container mounts (docs/recovery-plan.md section 4).
UNMOUNTED_DIRS=(open-webui postgres qdrant redis backups documents)

STAMP="$(date +%Y-%m-%d_%H%M)"
DEST="${BACKUP_DIR}/${STAMP}"
PARTIAL="${DEST}.partial"
STEP="setup"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

on_error() {
    log "ERROR: step '${STEP}' failed (line $1). Incomplete backup left at ${PARTIAL}"
}

cleanup() {
    # Best effort: never let cleanup hide the original exit status.
    docker exec "${PG_CONTAINER}" sh -c 'dropdb -U "$POSTGRES_USER" --if-exists "$1"' sh "${TEST_DB}" >/dev/null 2>&1 || true
    docker exec "${WEBUI_CONTAINER}" rm -f "${WEBUI_TMP}" >/dev/null 2>&1 || true
}

trap 'on_error ${LINENO}' ERR
trap cleanup EXIT

# Run SQL from stdin against a database in the Phase 2 Postgres container.
# An empty database name means the container's own POSTGRES_DB.
pg_sql() {
    docker exec -i "${PG_CONTAINER}" \
        sh -c 'psql -U "$POSTGRES_USER" -d "${1:-$POSTGRES_DB}" -XAtq -v ON_ERROR_STOP=1' sh "$1"
}

# Archive a host directory through ARCHIVE_IMAGE, read-only, as a gzipped tar
# streamed to stdout so the archive file is owned by the user running this.
# Extra arguments are passed to tar before the source path (e.g. --exclude).
archive_dir() {
    local src="$1" name="$2"
    shift 2
    docker run --rm --pull=never --network none --entrypoint tar \
        -v "${src}:/src:ro" "${ARCHIVE_IMAGE}" \
        czf - -C /src "$@" . >"${PARTIAL}/${name}.tar.gz"
    gzip -t "${PARTIAL}/${name}.tar.gz"
}

log "=== CLIVE backup ${STAMP} ==="

# --- Checks --------------------------------------------------------------
STEP="checks"
if ! [[ "${RETENTION_DAILY}" =~ ^[1-9][0-9]*$ && "${RETENTION_WEEKLY}" =~ ^[0-9]+$ ]]; then
    log "ERROR: BACKUP_RETENTION_DAILY must be >= 1 and BACKUP_RETENTION_WEEKLY >= 0"
    exit 1
fi
if [[ -n "${BACKUP_RETENTION_DAYS:-}" ]]; then
    log "WARNING: BACKUP_RETENTION_DAYS is no longer used; set BACKUP_RETENTION_DAILY and BACKUP_RETENTION_WEEKLY"
fi
for container in "${PG_CONTAINER}" "${WEBUI_CONTAINER}" "${OLLAMA_CONTAINER}"; do
    if [[ "$(docker inspect -f '{{.State.Running}}' "${container}" 2>/dev/null)" != "true" ]]; then
        log "ERROR: container ${container} is not running"
        exit 1
    fi
done

umask 077
mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"
if [[ "$(df --output=source "${BACKUP_DIR}" | tail -1)" == "$(df --output=source "${DATA_ROOT}" | tail -1)" ]]; then
    log "ERROR: ${BACKUP_DIR} is on the same disk as ${DATA_ROOT}; choose a target on the other disk"
    exit 1
fi
if [[ -e "${DEST}" || -e "${PARTIAL}" ]]; then
    log "ERROR: ${DEST} already exists; wait a minute and run again"
    exit 1
fi
mkdir "${PARTIAL}"
log "Writing to ${PARTIAL}"

# --- 1. Phase 2 Postgres -------------------------------------------------
STEP="postgres dump"
log "[1/7] Dumping the Phase 2 database and roles"
docker exec "${PG_CONTAINER}" sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' >"${PARTIAL}/pgvector.dump"
docker exec "${PG_CONTAINER}" sh -c 'pg_dumpall -U "$POSTGRES_USER" --globals-only' >"${PARTIAL}/postgres-globals.sql"

STEP="postgres restore check"
log "      Restore check into temporary database ${TEST_DB}"
docker exec -e PGOPTIONS='-c client_min_messages=warning' "${PG_CONTAINER}" \
    sh -c 'dropdb -U "$POSTGRES_USER" --if-exists "$1" && createdb -U "$POSTGRES_USER" "$1"' sh "${TEST_DB}"
docker exec -i "${PG_CONTAINER}" sh -c 'pg_restore -U "$POSTGRES_USER" -d "$1" --no-owner --exit-on-error' sh "${TEST_DB}" <"${PARTIAL}/pgvector.dump"
if [[ "$(echo "SELECT count(*) FROM pg_extension WHERE extname = 'vector';" | pg_sql "${TEST_DB}")" != "1" ]]; then
    log "ERROR: restored database has no vector extension"
    exit 1
fi
TABLES_SQL="SELECT format('%I.%I', schemaname, tablename) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') ORDER BY 1;"
if [[ "$(echo "${TABLES_SQL}" | pg_sql "")" != "$(echo "${TABLES_SQL}" | pg_sql "${TEST_DB}")" ]]; then
    log "ERROR: restored database has a different table list from the live one"
    exit 1
fi
while read -r table; do
    [[ -n "${table}" ]] || continue
    live="$(echo "SELECT count(*) FROM ${table};" | pg_sql "")"
    restored="$(echo "SELECT count(*) FROM ${table};" | pg_sql "${TEST_DB}")"
    if [[ "${live}" != "${restored}" ]]; then
        log "ERROR: ${table}: ${live} rows live, ${restored} restored"
        exit 1
    fi
    log "      ${table}: ${restored} rows (matches live)"
done < <(echo "${TABLES_SQL}" | pg_sql "${TEST_DB}")
docker exec "${PG_CONTAINER}" sh -c 'dropdb -U "$POSTGRES_USER" "$1"' sh "${TEST_DB}"

# --- 2. Open WebUI database ------------------------------------------------
STEP="webui.db online backup"
log "[2/7] Online backup of Open WebUI's webui.db"
docker exec "${WEBUI_CONTAINER}" python3 -c '
import sqlite3, sys
src = sqlite3.connect("file:/app/backend/data/webui.db?mode=ro", uri=True)
dst = sqlite3.connect(sys.argv[1])
src.backup(dst)
dst.execute("PRAGMA journal_mode=DELETE")
dst.close()
src.close()
' "${WEBUI_TMP}"
docker exec "${WEBUI_CONTAINER}" cat "${WEBUI_TMP}" >"${PARTIAL}/webui.db"
docker exec "${WEBUI_CONTAINER}" rm -f "${WEBUI_TMP}"
INTEGRITY="$(python3 -I -c '
import sqlite3, sys
con = sqlite3.connect(f"file:{sys.argv[1]}?mode=ro&immutable=1", uri=True)
print(con.execute("PRAGMA integrity_check").fetchone()[0])
' "${PARTIAL}/webui.db")"
if [[ "${INTEGRITY}" != "ok" ]]; then
    log "ERROR: webui.db integrity check: ${INTEGRITY}"
    exit 1
fi
log "      integrity_check: ok"

# --- 3. Open WebUI files ---------------------------------------------------
STEP="openwebui_data archive"
log "[3/7] Archiving ${DATA_ROOT}/openwebui_data (without the live webui.db)"
archive_dir "${DATA_ROOT}/openwebui_data" "openwebui_data" --exclude=./webui.db --exclude='./webui.db-*'

# --- 4. Unmounted directories ---------------------------------------------
log "[4/7] Archiving the unmounted ${DATA_ROOT} directories"
for dir in "${UNMOUNTED_DIRS[@]}"; do
    STEP="archive ${dir}"
    if [[ ! -d "${DATA_ROOT}/${dir}" ]]; then
        log "ERROR: ${DATA_ROOT}/${dir} not found; update UNMOUNTED_DIRS and docs/recovery-plan.md"
        exit 1
    fi
    archive_dir "${DATA_ROOT}/${dir}" "data-${dir}"
    log "      ${dir}"
done

# --- 5. .env ----------------------------------------------------------------
STEP="encrypt .env"
log "[5/7] .env"
if [[ -n "${GPG_RECIPIENT}" ]]; then
    gpg --batch --yes --quiet --trust-model always --encrypt \
        --recipient "${GPG_RECIPIENT}" --output "${PARTIAL}/env.gpg" "${ENV_FILE}"
    log "      encrypted to env.gpg"
else
    log "      WARNING: .env NOT backed up: BACKUP_GPG_RECIPIENT is not set (GPG key pair to be created later; docs/recovery-plan.md section 7)"
    echo ".env not backed up: BACKUP_GPG_RECIPIENT not set" >>"${PARTIAL}/NOTES.txt"
fi

# --- 6. Model list and image versions -------------------------------------
STEP="model list and images"
log "[6/7] Ollama model list and image digests"
docker exec "${OLLAMA_CONTAINER}" ollama list >"${PARTIAL}/ollama-models.txt"
{
    for container in $(docker ps --format '{{.Names}}' | sort); do
        image_id="$(docker inspect -f '{{.Image}}' "${container}")"
        echo "${container} $(docker inspect -f '{{.Config.Image}}' "${container}") $(docker image inspect -f '{{join .RepoDigests ","}}' "${image_id}")"
    done
} >"${PARTIAL}/images.txt"

# --- 7. Manifest -------------------------------------------------------------
STEP="manifest"
log "[7/7] Writing and verifying MANIFEST.txt"
cd "${PARTIAL}"
mapfile -t files < <(find . -type f -printf '%P\n' | sort)
stat -c '%s  %n' "${files[@]}" >SIZES.txt
sha256sum "${files[@]}" SIZES.txt >MANIFEST.txt
sha256sum --quiet --strict -c MANIFEST.txt
cd "${REPO_DIR}"
mv "${PARTIAL}" "${DEST}"
log "Backup complete: ${DEST} ($(du -sh "${DEST}" | cut -f1))"

# --- Retention ---------------------------------------------------------------
# Keep the newest backup of each of the last RETENTION_DAILY days that have a
# backup, plus the newest backup of each of the last RETENTION_WEEKLY Sundays.
# Only completed backup folders (YYYY-MM-DD_HHMM) are considered; .partial
# folders are left for inspection.
STEP="retention"
declare -A keep=() days=() sundays=()
mapfile -t backups < <(find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d \
    -regextype posix-extended -regex '.*/[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}' -printf '%f\n' | sort -r)
for b in "${backups[@]}"; do
    day="${b%_*}"
    if [[ -z "${days[${day}]+x}" ]] && ((${#days[@]} < RETENTION_DAILY)); then
        days[${day}]=1
        keep[${b}]=1
    fi
    if [[ "$(date -d "${day}" +%u)" == "7" && -z "${sundays[${day}]+x}" ]] && ((${#sundays[@]} < RETENTION_WEEKLY)); then
        sundays[${day}]=1
        keep[${b}]=1
    fi
done
deleted=0
for b in "${backups[@]}"; do
    if [[ -z "${keep[${b}]+x}" ]]; then
        rm -rf -- "${BACKUP_DIR:?}/${b}"
        deleted=$((deleted + 1))
    fi
done
log "Retention: kept ${#keep[@]}, deleted ${deleted} (${RETENTION_DAILY} daily, ${RETENTION_WEEKLY} weekly)"
mapfile -t partials < <(find "${BACKUP_DIR}" -mindepth 1 -maxdepth 1 -type d -name '*.partial' -printf '%f\n')
if ((${#partials[@]} > 0)); then
    log "WARNING: incomplete backups to inspect and remove: ${partials[*]}"
fi
log "=== Done ==="
