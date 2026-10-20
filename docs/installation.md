# CLIVE Installation & Setup Guide (Phases 1–3)

Target environment: Ubuntu Desktop 24.04 LTS, Python 3.12.3, Docker + Docker Compose.

## 1. Prerequisites

- Docker & Docker Compose installed
- Python 3.12.3
- `uv` for Python package management
- NVIDIA drivers + Container Toolkit (for the Ollama GPU reservation, if using GPU inference)
- Git

## 2. Clone the Repository

```bash
git clone git@github.com:cvc-arus/CLIVE-I.git
cd CLIVE-I
git checkout develop
```

## 3. Root Environment File

Create `.env` at the repo root from `.env.example`, which lists every key needed to install the system:

```bash
cp .env.example .env
```

Fill in real values for the keys that `docker-compose.yml` references directly:

- Phase 1/2 PGVector: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.
- Phase 3 mock database: `SIMPRO_MOCK_DB_USER`, `SIMPRO_MOCK_DB_PASSWORD`, `SIMPRO_MOCK_DB_NAME`. Compose builds the mock's `SIMPRO_MOCK_DATABASE_URL` from them, so use URL-safe characters only (no `@`, `:`, `/`, `%`). `docker compose` refuses to start if any of them is unset.

Postgres applies `SIMPRO_MOCK_DB_*` only when it first creates the `simpro-mock-db-data` volume. If you change them later, recreate that volume (section 10).

The `SIMPRO_` client keys can be left at their mock defaults for local development.

All published ports bind to `127.0.0.1` and are reachable only from the host.

## 4. Start the Full Stack

```bash
docker compose up -d
```

This brings up, in dependency order:
1. `postgres` (PGVector) — waits for healthy before `open-webui` starts
2. `simpro-mock-db` — waits for healthy before `simpro-mock` starts (`simpro-mock` has its own healthcheck on `GET /health`)
3. `ollama`, `tika` — no dependencies
4. `open-webui` — depends on `postgres` (healthy), `tika`, `ollama`
5. `simpro-mock` — depends on `simpro-mock-db` (healthy); its container `CMD` runs `alembic upgrade head`, then `python -m simpro_mock.seed`, then `uvicorn` — so the mock is fully migrated and seeded by the time it's reachable

## 5. Verify Phase 1 & 2

```bash
./scripts/verify.sh
```

Checks Ollama and the PGVector database respond correctly. Pull a model if needed:

```bash
docker exec -it clive-ollama ollama pull llama3.2
docker exec -it clive-ollama ollama pull nomic-embed-text
```

Open WebUI: http://localhost:3000

## 6. Verify Phase 3 (Simpro Mock)

```bash
curl http://localhost:8100/health
uv run python scripts/verify-simpro-mock.py
```

`verify-simpro-mock.py` obtains a token, exercises every resource endpoint, and exits non-zero with diagnostics on failure.

## 7. Install `simpro_client` for Local Development

```bash
uv sync
```

`uv sync` creates `.venv/` and installs the package plus the `dev` dependency group.

**Note:** the root `pyproject.toml` defines `[dependency-groups] dev = [...]` (PEP 735 style) rather than `[project.optional-dependencies]`, so `pip install -e ".[dev]"` and `uv pip install -e ".[dev]"` warn that there is no `dev` extra and skip the dev dependencies. Use `uv sync`.

## 8. Run the Test Suite

```bash
uv run pytest -q -m "not integration"
```

This runs the offline suite (no live services required). To also run the live mock smoke test:

```bash
docker compose up -d --build simpro-mock
uv run pytest tests/test_simpro_mock_v2.py -v
```

Test layers and markers are described in `docs/testing.md`.

## 9. Backups

```bash
./scripts/backup.sh
```

Backs up everything in the inventory in `docs/recovery-plan.md` §7 to `BACKUP_DIR` (default `~/clive-backups`), which must be on a different disk from `/data`: the Phase 2 database (restore-verified into a temporary database), Open WebUI's `webui.db` (online backup) and files, the unmounted `/data` directories, the Ollama model list and image digests, with a SHA-256 `MANIFEST.txt`. Each run writes `<BACKUP_DIR>/<YYYY-MM-DD_HHMM>/` and keeps 7 daily and 4 weekly (Sunday) backups. Settings are the `BACKUP_*` variables in `.env.example`; `BACKUP_RETENTION_DAYS` is no longer used.

`.env` is backed up only when `BACKUP_GPG_RECIPIENT` names a GPG public key; until then the script logs a warning and skips it.

Check a backup:

```bash
cd ~/clive-backups/<YYYY-MM-DD_HHMM> && sha256sum -c MANIFEST.txt
```

### Daily schedule

A systemd timer runs the backup daily at 02:30 as the repository's owner. The unit files are in `deploy/systemd/`; the service is a template whose `<repo-dir>` and `<user>` placeholders are filled in at install time (ADR-017). Install them from the repository root (needs sudo), or re-install after changing them:

```bash
sed -e "s|<repo-dir>|$PWD|g" -e "s|<user>|$(id -un)|g" deploy/systemd/clive-backup.service \
    | sudo install -m 0644 /dev/stdin /etc/systemd/system/clive-backup.service
sudo install -m 0644 deploy/systemd/clive-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now clive-backup.timer
systemctl list-timers clive-backup.timer
```

Run it once through systemd and read the log:

```bash
sudo systemctl start clive-backup.service
journalctl -u clive-backup -n 30 --no-pager
```

The service runs `scripts/backup.sh` from the repository working tree, so the script on the checked-out branch is the one that runs. Remove the schedule with `sudo systemctl disable --now clive-backup.timer`, then delete the two files from `/etc/systemd/system/` and run `sudo systemctl daemon-reload`; existing backups are not touched.

To restore a backup, or to check one with a restore drill next to the live stack (`deploy/restore-drill/compose.yml`), follow `docs/recovery-plan.md` §10.

### Disk health

`smartmontools` monitors both disks (`docs/recovery-plan.md` §9). The tracked `deploy/smartd/smartd.conf` holds `<os-disk-by-id>` and `<data-disk-by-id>` placeholders (ADR-017); the host's copy with the real IDs is the untracked `deploy/smartd/smartd.conf.local`. Create it once (`ls -l /dev/disk/by-id/ | grep -v part` lists the IDs), then install it (needs sudo):

```bash
cp deploy/smartd/smartd.conf deploy/smartd/smartd.conf.local   # first time only; fill in the IDs
sudo apt install smartmontools
sudo smartd -q onecheck -c deploy/smartd/smartd.conf.local
sudo cp /etc/smartd.conf /etc/smartd.conf.orig
sudo install -m 0644 deploy/smartd/smartd.conf.local /etc/smartd.conf
sudo systemctl restart smartmontools
systemctl status smartmontools --no-pager
```

`smartd.conf.local` names the disks by serial number (`/dev/disk/by-id/`); edit it when a disk is replaced, and keep the tracked template's comments and directives in step. Warnings go to the journal only (`journalctl -u smartmontools`). Rollback: `sudo mv /etc/smartd.conf.orig /etc/smartd.conf` and `sudo apt remove smartmontools`.

The mock's database (`simpro-mock-db`) is disposable dev/test data and is not part of the backup strategy — it can always be rebuilt from the seed script.

## 10. Rollback

```bash
docker compose down            # stop all services, keep volumes
docker compose down -v         # stop all services AND remove the named volumes in docker-compose.yml
```

`-v` removes the named volumes declared in `docker-compose.yml` (only `simpro-mock-db-data`, which holds the mock's database). It does not remove the Phase 1/2 bind mounts under `/data/` (`/data/ollama`, `/data/openwebui_data`, `/data/pgvector_data`). Get Alex's approval before running it.

For `simpro-mock` specifically, since its data is fully reproducible from `seed.py`:

```bash
docker compose stop simpro-mock simpro-mock-db
docker volume rm clive-i_simpro-mock-db-data   # volume name may vary; check `docker volume ls`
docker compose up -d simpro-mock-db simpro-mock
```

## 11. Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `simpro-mock` serves old code after an edit | Dockerfile bakes source at build time | `docker compose build simpro-mock` then `up -d`, not just a restart |
| `uv run ENV_VAR=... command` fails, tries to exec the env var | Argument order | Use `ENV_VAR=... uv run command` |
| `pip install -e ".[dev]"` warns "does not provide the extra 'dev'" | Root `pyproject.toml` uses `[dependency-groups]`, not `[project.optional-dependencies]` | Use `uv sync` |
| 401 from the mock | Missing/incorrect `Authorization: Bearer <token>` header, or token doesn't match `SIMPRO_MOCK_MOCK_ACCESS_TOKEN` | Re-fetch a token from `/oauth2/token` |
