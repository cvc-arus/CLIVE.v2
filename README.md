# CLIVE – Enterprise AI Platform

A production-ready, fully self-hosted Enterprise AI Platform for a CCTV and security company (CVC).

The platform is designed to be modular, reproducible, scalable, and built entirely using free and open-source software. It provides a secure on-premises AI environment capable of document retrieval, knowledge management, business automation, and future multi-agent workflows.

---

## Project Goals

- Build a fully self-hosted AI platform
- Keep all company data on-premises
- Use Docker-first deployment
- Support Retrieval-Augmented Generation (RAG)
- Integrate with Simpro via API
- Generate company-specific documentation
- Scale from a single workstation to enterprise hardware
- Maintain production-quality documentation and architecture

---

## Current Status

### ✅ Phase 1 – Complete

- Ubuntu 24.04 LTS
- Docker & Docker Compose
- Ollama
- Open WebUI
- Local LLM inference

### ✅ Phase 2 – Complete

Production RAG infrastructure

- PostgreSQL + PGVector
- Apache Tika
- Local Ollama embeddings (`nomic-embed-text`)
- Open WebUI Knowledge Base
- Hybrid Search
- Tuned chunking
- Automated backup & restore verification

### ⏳ Planned

- Phase 3 – Simpro API Integration
- Phase 4 – Document Generation
- Phase 5 – Security & Reverse Proxy
- Phase 6 – AI Sales Agent
- Phase 7 – Public Tender Agent
- Phase 8 – Customer Intelligence
- Phase 9 – Multi-Agent Architecture
- Phase 10 – Monitoring, Backup & Disaster Recovery

---

# Objectives

The completed platform will provide:

- Local AI inference
- Enterprise document search
- Knowledge Base for 5,000+ documents
- Technical document generation
- API integrations
- AI-assisted engineering
- AI-assisted sales
- Tender analysis
- Customer intelligence
- Future multi-agent workflows

---

# Hardware

## Current Development Server

- Intel i5-10400
- NVIDIA RTX 3080 (10 GB)
- 32 GB RAM
- Ubuntu Desktop 24.04 LTS
- 2 × 223 GB SSD

## Future Production Hardware

- AMD Threadripper
- NVIDIA RTX 5090
- 128–256 GB RAM

The platform is designed to scale without requiring architectural changes.

---

# Technology Stack

| Component | Purpose |
|----------|---------|
| Ubuntu 24.04 LTS | Operating System |
| Docker | Container platform |
| Docker Compose | Service orchestration |
| Ollama | Local LLM runtime |
| Open WebUI | AI interface |
| PostgreSQL | Database |
| PGVector | Vector database |
| Apache Tika | Document extraction |
| Git | Version control |

---

# Repository Structure

```text
.
├── backups
│   └── clive_pgvector_20260805_160501.sql.gz
├── CLAUDE.md
├── configs
│   └── postgres
│       └── init-pgvector.sql
├── dock
│   └── phase1
├── docker-compose.yml
├── docs
│   ├── ADR
│   │   ├── adr-001-local-llm-stack.md
│   │   ├── adr-002-vector-database-pgvector.md
│   │   ├── adr-003-document-extraction-tika.md
│   │   ├── adr-004-http-client-choice.md
│   │   ├── adr-005-auth-strategy.md
│   │   ├── adr-006-library-first-architecture.md
│   │   ├── adr-007-configuration-management.md
│   │   ├── adr-008-rate-limiting-strategy.md
│   │   ├── adr-009-phase3-phase4-handoff.md
│   │   ├── adr-010-resilience-policy.md
│   │   ├── ADR-index.md
│   │   └── adr-mock-simpro-api.md
│   ├── architecture.md
│   ├── CHANGELOG.md
│   ├── CLAUDE.md
│   ├── development-standards.md
│   ├── installation.md
│   ├── known-issues.md
│   ├── PDDs
│   │   ├── PDD-phase1.md
│   │   ├── PDD-phase2.md
│   │   ├── PDD-phase3.md
│   │   └── PDD-phase4.md
│   ├── phase1
│   │   └── summary.md
│   ├── phase2
│   │   └── summary.md
│   ├── phase3
│   │   ├── logging.md
│   │   ├── phase3-sprint4-2-typed-python-SDK-endpoint-layer.md
│   │   ├── phase3-sprint4-4-pagiantion and retries.md
│   │   ├── phase3-sprint4-architecture-summary.md
│   │   ├── phase3-sprint4-contract.md
│   │   ├── phase3-sprint4.md
│   │   ├── phase3-sprint4-preflight-audit.md
│   │   └── phase3-summary.md
│   ├── README.md
│   ├── roadmap.md
│   ├── scope
│   │   └── scope&readmap-rev2.md
│   ├── simpro-mock-api-reference.md
│   └── testing.md
├── pyproject.toml
├── README.md
├── scripts
│   ├── backup.sh
│   ├── verify.sh
│   └── verify-simpro-mock.py
├── services
│   └── simpro_mock
│       ├── alembic
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions
│       ├── alembic.ini
│       ├── CLAUDE.md
│       ├── configuration.md
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── simpro_mock
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── filtering.py
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── middleware.py
│       │   ├── models.py
│       │   ├── routers.py
│       │   ├── schemas.py
│       │   └── seed.py
│       └── uv.lock
├── src
│   ├── simpro_client
│   │   ├── auth.py
│   │   ├── CLAUDE.md
│   │   ├── client.py
│   │   ├── config.py
│   │   ├── endpoints
│   │   │   ├── asset.py
│   │   │   ├── attachment.py
│   │   │   ├── base.py
│   │   │   ├── company.py
│   │   │   ├── contact.py
│   │   │   ├── customer.py
│   │   │   ├── employee.py
│   │   │   ├── __init__.py
│   │   │   ├── job_note.py
│   │   │   ├── job.py
│   │   │   ├── project.py
│   │   │   ├── quote.py
│   │   │   ├── site.py
│   │   │   └── status.py
│   │   ├── exceptions.py
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── models
│   │   │   ├── asset.py
│   │   │   ├── attachment.py
│   │   │   ├── base.py
│   │   │   ├── company.py
│   │   │   ├── contact.py
│   │   │   ├── customer.py
│   │   │   ├── employee.py
│   │   │   ├── __init__.py
│   │   │   ├── job_note.py
│   │   │   ├── job.py
│   │   │   ├── project.py
│   │   │   ├── quote.py
│   │   │   ├── site.py
│   │   │   └── status.py
│   │   └── rate_limiter.py
│   └── simpro_client.egg-info
│       ├── dependency_links.txt
│       ├── PKG-INFO
│       ├── requires.txt
│       ├── SOURCES.txt
│       └── top_level.txt
├── structure.txt
├── tests
│   ├── CLAUDE.md
│   ├── conftest.py
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_endpoints.py
│   ├── test_logging.py
│   ├── test_manual_logging.py
│   ├── test_models.py
│   ├── test_pagination.py
│   ├── test_rate_limiter.py
│   ├── test_retries.py
│   ├── test_route_contract.py
│   └── test_simpro_mock_v2.py
└── uv.lock

25 directories, 122 files

```

---

# Roadmap

| Phase | Description | Status |
|--------|-------------|--------|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG Knowledge Base | ✅ Complete |
| 3 | Simpro API Integration | Planned |
| 4 | AI Document Generation | Planned |
| 5 | Security & Reverse Proxy | Planned |
| 6 | AI Sales Agent | Planned |
| 7 | Public Tender Agent | Planned |
| 8 | Customer Intelligence | Planned |
| 9 | Multi-Agent Architecture | Planned |
| 10 | Monitoring & Disaster Recovery | Planned |

---

# Engineering Principles

- Open Source First
- Self Hosted
- Docker First
- API First
- Infrastructure as Code
- Git Version Controlled
- Modular Architecture
- Production Ready
- Enterprise Quality
- Fully Documented
- Reproducible
- Future Scalable

No cloud AI providers unless explicitly approved.

---

# Development Standards

Every phase follows the same workflow:

1. Design
2. Architecture
3. Documentation
4. Trade-off Analysis
5. Implementation
6. Verification
7. Rollback Procedure
8. Documentation Update
9. Git Commit

Each sprint includes:

- Goal
- Business Value
- Tasks
- Commands
- Configuration
- Folder Structure
- Files Created
- Verification
- Common Issues
- Rollback Procedure
- Acceptance Criteria

---

# Planned Features

## Local LLM Platform

- Self-hosted inference
- Multi-model support
- Local APIs
- Future multi-agent orchestration

## Knowledge Base

Supports:

- PDFs
- Word documents
- RAMS
- Contracts
- Tender responses
- Drawings
- Equipment specifications
- Certificates
- Templates
- Case studies

Features:

- Metadata
- Versioning
- Hybrid Search
- Local vector storage

## Simpro Integration

- Project data
- Customer data
- Equipment data
- Reporting
- Analytics
- API integration

## Document Generation

Generate:

- Quotes
- RAMS
- Contracts
- Equipment specifications
- Tender responses
- Technical documentation
- Compliance documentation

## AI Sales Agent

- Prospect discovery
- Company research
- Lead qualification
- Lead scoring
- CRM-ready summaries

## Public Tender Agent

- Monitor tender portals
- Analyse opportunities
- Prioritise bids
- Prepare supporting documentation

## Customer Intelligence

Analyse:

- Industries
- Geography
- Company size
- Technology stack
- Pain points
- Buying triggers
- Decision makers

Generate:

- Ideal Customer Profile (ICP)
- Negative ICP
- Sales documentation
- Qualification criteria

---

# Security

- Docker isolation
- Least privilege
- Environment variables
- SSH keys
- HTTPS (planned)
- Nginx reverse proxy (planned)
- Firewall (planned)
- Minimal exposed ports

---

# Documentation

The project maintains documentation for:

- Project Design Document (PDD)
- Architecture
- Architecture Decision Records (ADRs)
- Docker
- Networking
- Security
- Knowledge Base
- Installation Guide
- Backup Strategy
- Disaster Recovery
- Development Standards
- Roadmap
- Change Log

---

# Long-Term Vision

CLIVE aims to become a fully self-hosted Enterprise AI Platform capable of supporting engineering, operations, sales, document management, and business intelligence while ensuring all company data remains private and under local control.