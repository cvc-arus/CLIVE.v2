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
ai-platform/
│
├── phase1/
│   ├── README.md
│   ├── docker-compose.yml
│   └── structure.txt
│
├── phase2/
│   ├── README.md
│   ├── docker-compose.yml
│   ├── configs/
│   ├── scripts/
│   ├── backups/
│   └── docs/
│
├── docs/
│
├── CHANGELOG.md
├── ROADMAP.md
└── README.md
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