# CLIVE-I: Multi-Phase Database & Simpro API Client System

A comprehensive, production-grade platform combining a secure local vector database (Phase 2) with a modular, highly observable Simpro REST API Python integration client (Phase 3).

---

## 📂 Directory Structure

This project isolates system containers, database initialization configs, automated backup utilities, and the core Python package:

```text
.
├── docker-compose.yml       # Docker environment for Postgres & Ollama
├── backups/                 # Compressed database backups
│   └── clive_pgvector_20260805_160501.sql.gz
├── configs/
│   └── postgres/
│       └── init-pgvector.sql # Initial database and pgvector extension config
├── docs/                    # Architectural documents
│   ├── phase1.md            # Local AI / LLM workspace design
│   └── phase2.md            # Vector Database architecture design
├── phase3-logging.md       # Diagnostic and logging specifications
├── pyproject.toml           # Package definitions, build backends, linter, and pytest setups
├── README.md                # This file
├── scripts/                 # Bash administrative tools
│   ├── backup.sh            # Gzipped PostgreSQL backup engine
│   └── verify.sh            # Local Ollama & DB connection sanity check
├── src/
│   ├── simpro_client/       # Reusable integration client package
│   │   ├── __init__.py      # Package entry point and namespace manager
│   │   ├── auth.py          # OAuth2 token manager (caching and API key fallbacks)
│   │   ├── client.py        # Base HTTP Client (auth injection, auto 401 refresh, retries)
│   │   ├── config.py        # SettingsConfigLoader with Pydantic-Settings (ignores extras)
│   │   ├── exceptions.py    # Custom typed Exception hierarchy
│   │   └── logging.py       # Thread-safe ContextVar correlation ID JSON Logger
│   └── simpro_client.egg-info/ # Editable install metadata
└── tests/                   # Automated offline test suites
    ├── __init__.py
    ├── conftest.py          # Shared mock environment settings and respx fixtures
    ├── test_auth.py         # 5 tests proving token caching and fallback cycles
    ├── test_client.py       # 5 tests checking HTTP verbs and 401/429 error flows
    ├── test_config.py       # 3 tests validating Pydantic environment constraints
    ├── test_logging.py      # 5 tests checking correlation ID ContextVar isolation
    └── test_manual_logging.py # Interactively verifies raw JSON log output
```

---

## 🛠️ Phases 1 & 2: Local AI & Vector Database Setup

This layer is responsible for running vector storage services locally, allowing clean embeddings generation.

### Services Managed
- **PostgreSQL Database:** Powered by the official pgvector tag with customized memory tuning.
- **Ollama Engine:** Runs lightweight language models (such as Qwen) completely offline.

### Quick Start (DB & Container Services)
1. Boot up the local database and Ollama containers:
   ```bash
   docker compose up -d
   ```
2. Confirm both services communicate cleanly by executing the verification utility:
   ```bash
   ./scripts/verify.sh
   ```
3. Backup your current PGVector database state:
   ```bash
   ./scripts/backup.sh
   ```

---

## 🔌 Phase 3: Simpro API Client Foundation

The Python package `simpro_client` provides a secure, fully mock-tested, and optimized integration client to communicate cleanly with Simpro endpoints.

### Installation
Activate your virtual environment and install the package along with its development and linting tools in editable mode:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Configuration (coexistence-safe)
The configuration is parsed using `pydantic-settings` from your root `.env` file. It loads all fields prefixed with `SIMPRO_` and uses `extra="ignore"`, allowing Simpro parameters to safely coexist with PostgreSQL credentials without throwing validation errors.

Append the following keys to your root `.env`:
```env
# Simpro Connection Config
SIMPRO_BASE_URL=http://simpro-mock:8000/api/v1.0
SIMPRO_TOKEN_URL=http://simpro-mock:8000/oauth2/token

# OAuth2 Credentials
SIMPRO_CLIENT_ID=your-client-id-here
SIMPRO_CLIENT_SECRET=your-client-secret-here

# Authentication Strategy ('client_credentials' or 'api_key')
SIMPRO_AUTH_MODE=client_credentials
```

---

## 📊 Core Features & Observability

### 1. Robust Token Caching & Autorefresh
The `AuthManager` caches token strings in memory and checks the expiry timestamp before every API call. If a stale token is used and a `401 Unauthorized` is returned, the base HTTP Client automatically invalidates the cache, requests a new token, and retries the request exactly once.

### 2. Transaction Correlation IDs
Every request is mapped with a thread-safe and async-safe transaction `correlation_id` via Python's `ContextVar`. You can explicitly assign a trace ID to link multiple operations or let the client auto-generate a random 12-character hex fragment at startup:

```python
from simpro_client.logging import set_correlation_id

set_correlation_id("invoice-sync-01")
```

### 3. Machine-Parseable JSON Logs
By calling `configure_logging()`, all system events are printed to `stderr` as single-line serialized JSON elements. These elements are easily filtered on monitoring dashboards (e.g., Datadog, CloudWatch, or Grafana):

```json
{"timestamp": "2026-08-18 14:43:08,211", "level": "INFO", "logger": "simpro_client", "message": "GET /companies/1/jobs/ -> 200 (45.2ms)", "correlation_id": "invoice-sync-01", "method": "GET", "url": "/companies/1/jobs/", "status_code": 200, "duration_ms": 45.2}
```

---

## 🧪 Testing and Linting Pipeline

All codebase modifications must pass zero-error linting and testing checks before verification.

### Run Automated Testing (18 Passed)
Tests run entirely offline by intercepting outgoing traffic using `respx`:
```bash
pytest tests/ -v
```

### Run Code Linting & Formatting
Strict guidelines are enforced using `Ruff`:
```bash
# Analyze code issues and sort import lines automatically
ruff check src/ --fix

# Re-format code blocks
ruff format src/
```
