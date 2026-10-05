# CLIVE — Enterprise AI Platform for CVC

CLIVE is a self-hosted AI platform built for **CVC**, a CCTV and security
company. It brings large language models, document search and business-system
integration together on hardware CVC owns, so that company knowledge,
customer data and commercial documents never leave the building.

The long-term aim is for CLIVE to support CVC's whole operational workflow:
finding answers in company documents, drafting quotes, RAMS, contracts and
tender responses from real project data, and later helping with sales and
tender discovery through AI agents.

> **Status:** CLIVE is built in phases. The current status of every phase is
> kept in one place: [`docs/roadmap.md`](docs/roadmap.md).

---

## Why CLIVE exists

CVC produces a large volume of technical and commercial documents (RAMS,
quotes, contracts, tender responses, equipment specifications), and much of
the knowledge needed to write them lives in past documents and in Simpro,
the company's job-management system. CLIVE is designed to:

- make roughly 5,000+ company documents searchable and usable by an AI
  assistant
- connect AI tools to live business data from Simpro
- generate first drafts of company documents from that knowledge and data
- do all of this **on-premises**, with open-source software and no cloud AI
  provider unless explicitly approved

---

## Platform modules

| Module | What it does | Phase |
|---|---|---|
| Local AI platform | Runs open-source LLMs locally (Ollama) with a chat interface (Open WebUI) | 1 |
| Knowledge base (RAG) | Extracts text from company documents (Apache Tika), embeds it (`nomic-embed-text`) and stores it in PostgreSQL + PGVector for hybrid search | 2 |
| Simpro integration | A typed Python client (`simpro_client`) for Simpro's REST API, plus a local mock of that API for development | 3 |
| Document generation | Drafts quotes, RAMS, contracts, equipment specifications, tender responses and technical documents from Simpro data and the knowledge base | 4 |
| Security & reverse proxy | Nginx, HTTPS, firewall and authentication | 5 |
| AI sales agent | Prospect discovery, company research, lead qualification and scoring | 6 |
| Public tender agent | Monitors tender portals, extracts requirements, analyses bid fit | 7 |
| Customer intelligence | Analyses existing customers to build ideal customer profiles and qualification criteria | 8 |
| Multi-agent architecture | Orchestrates the agents above into combined workflows | 9 |
| Monitoring & disaster recovery | Health monitoring, backups and recovery | 10 |

See [`docs/roadmap.md`](docs/roadmap.md) for which phases are complete, in
progress or planned.

---

## How it fits together

```text
                         ┌──────────────────────────────┐
   Users ──────────────► │  Open WebUI  (chat + RAG UI) │
                         └──────┬───────────┬───────────┘
                                │           │
                  LLM + embeddings          document text + vectors
                                │           │
                     ┌──────────▼──┐   ┌────▼───────────────┐   ┌──────────────┐
                     │   Ollama    │   │ PostgreSQL+PGVector│   │ Apache Tika  │
                     │ (local LLMs)│   │  (knowledge base)  │◄──│ (extraction) │
                     └─────────────┘   └────────────────────┘   └──────────────┘

   simpro_client (Python library) ── HTTP ──►  simpro-mock  (FastAPI + own Postgres)
                                        └──►  real Simpro API (when access is enabled)
```

**Why a Simpro mock?** CVC does not yet have Simpro API access. The mock
reproduces Simpro's API (12 resources, pagination headers, filtering, bearer
auth) so the client can be built and tested now. When real access arrives,
the client is pointed at Simpro by changing configuration only; no client
code changes are needed. The reasoning is recorded in
[`docs/ADR/adr-mock-simpro-api.md`](docs/ADR/adr-mock-simpro-api.md).

Full detail: [`docs/architecture.md`](docs/architecture.md).

---

## Services

All services run in Docker Compose ([`docker-compose.yml`](docker-compose.yml)).

| Service | Container | Purpose | Host port |
|---|---|---|---|
| `ollama` | `clive-ollama` | Local LLM and embedding runtime | 11435 |
| `open-webui` | `clive-webui` | Chat and knowledge-base interface | 3000 |
| `postgres` | `clive-postgres` | PostgreSQL + PGVector knowledge base | 5432 (localhost only) |
| `tika` | `clive-tika` | Document text extraction | 9998 (localhost only) |
| `simpro-mock` | `clive-simpro-mock` | Mock Simpro REST API | 8100 |
| `simpro-mock-db` | `clive-simpro-mock-db` | Database for the mock only | 5433 |

---

## Technology

| Area | Tools |
|---|---|
| Host | Ubuntu 24.04 LTS, Docker, Docker Compose |
| AI | Ollama, Open WebUI, `nomic-embed-text` embeddings |
| Data | PostgreSQL 16, PGVector, Apache Tika |
| Simpro client | Python 3.12, httpx, Pydantic, pydantic-settings (synchronous) |
| Simpro mock | FastAPI, SQLAlchemy 2.0 (synchronous), Alembic, PostgreSQL |
| Quality | pytest, respx, ruff, uv |

Architecture decisions and their reasons are recorded as ADRs in
[`docs/ADR/`](docs/ADR/ADR-index.md).

---

## Getting started

You need an Ubuntu 24.04 machine with Docker and Docker Compose, Git,
Python 3.12 and `uv`. For GPU inference you also need NVIDIA drivers and the
NVIDIA Container Toolkit. The full list is in
[`docs/installation.md`](docs/installation.md) §1.

```bash
git clone https://github.com/cvc-arus/CLIVE-I.git
cd CLIVE-I
```

Then follow [`docs/installation.md`](docs/installation.md). It covers the
`.env` file, starting the stack, verifying each phase, setting up
`simpro_client` for development, backups and rollback.

Run the offline test suite (no Docker or network needed):

```bash
uv sync
uv run pytest -q -m "not integration"
```

Testing layers and options: [`docs/testing.md`](docs/testing.md).

---

## Repository layout

| Path | Contents |
|---|---|
| `src/simpro_client/` | Simpro API client library |
| `services/simpro_mock/` | Mock Simpro API service (own `pyproject.toml`, Dockerfile, migrations) |
| `tests/` | Test suite for `simpro_client` |
| `configs/` | Service configuration (PostgreSQL / PGVector init) |
| `scripts/` | Backup and verification scripts |
| `docs/` | All project documentation |
| `docker-compose.yml` | The full service stack |

Complete file tree: [`structure.txt`](structure.txt).

---

## Documentation

Start with the documentation index, [`docs/README.md`](docs/README.md). It
lists every document, what it covers and whether it is kept up to date.

| Document | Covers |
|---|---|
| [`docs/roadmap.md`](docs/roadmap.md) | Phases and their status |
| [`docs/architecture.md`](docs/architecture.md) | How the platform is built |
| [`docs/installation.md`](docs/installation.md) | Setting up and running the stack |
| [`docs/development-standards.md`](docs/development-standards.md) | Coding, tooling, Git and the sprint template |
| [`docs/testing.md`](docs/testing.md) | How the code is tested |
| [`docs/ADR/ADR-index.md`](docs/ADR/ADR-index.md) | Architecture decisions |
| [`docs/known-issues.md`](docs/known-issues.md) | Open issues and discrepancies |
| [`docs/CHANGELOG.md`](docs/CHANGELOG.md) | What changed, sprint by sprint |

---

## How the project is run

CLIVE is designed, documented and built one phase and one sprint at a time.

- **Design before code.** Each phase has a design document
  ([`docs/PDDs/`](docs/PDDs/)) and each sprint has an approved plan before
  implementation.
- **Decisions are recorded** as ADRs, with the alternatives considered.
- **Everything is reproducible:** Docker Compose, pinned dependencies,
  configuration through `.env` files, and no secrets in Git.
- **Documentation is part of done:** a sprint is complete only after its
  documentation update and commit.

Engineering principles: open source first, self-hosted, Docker first,
API first, modular, fully documented, and designed to scale.

### Working with Claude Code

The repository includes instructions for Claude Code: a root
[`CLAUDE.md`](CLAUDE.md) plus directory-specific `CLAUDE.md` files in
`docs/`, `src/simpro_client/`, `services/simpro_mock/` and `tests/`. The
`/doc-check` command (`.claude/commands/doc-check.md`) checks the
documentation against the code without editing anything.

---

## Hardware

| | Current development server | Planned production |
|---|---|---|
| CPU | Intel i5-10400 | AMD Threadripper |
| GPU | NVIDIA RTX 3080 (10 GB) | NVIDIA RTX 5090 |
| RAM | 32 GB | 128–256 GB |
| Storage | 2 × 223 GB SSD | — |
| OS | Ubuntu Desktop 24.04 LTS | — |

The architecture is designed to move to the production hardware without
redesign.

---

## Ownership

CLIVE is an internal CVC project. No licence has been published for this
repository.