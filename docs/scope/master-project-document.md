> Historical record: original project source document, added to the repository on 2026-10-01 (decision 1, `docs/README.md` §8). Not maintained; see `docs/roadmap.md` for current scope.

# CLIVE Enterprise AI Platform

## Master Project Document

---

# 1. Project Overview

## Project Name

**CLIVE**

## Company

**CVC**

## Industry

CCTV and Security

## Vision

Build a production-ready, fully self-hosted Enterprise AI Platform capable of automating knowledge management, document creation, bid writing, tender analysis, sales intelligence, and business automation while keeping all company data on-premises.

The platform must:

* Be completely self-hosted
* Use only free and open-source software
* Be modular
* Be reproducible
* Be fully documented
* Scale from the current development workstation to future enterprise hardware

---

# 2. Current Status

## Phase 1 (Completed)

Infrastructure deployed:

* Ubuntu Desktop 24.04 LTS
* Docker Compose
* Ollama
* Open WebUI

Current limitations:

* No Simpro API integration
* No production RAG
* No enterprise document indexing
* No vector database
* No AI agents

Current repository structure:

```text
.
├── docker-compose.yml
├── README.md
└── structure.txt
└── structure.txt
```

---

# 3. Hardware

## Current Development Machine

CPU

* Intel i5-10400

GPU

* RTX 3080 10GB

RAM

* 32GB

Storage

* 2 × 223GB SSD

Operating System

* Ubuntu Desktop 24.04 LTS

---

## Future Upgrade

* RTX 5090
* Threadripper
* 128–256GB RAM

All architecture decisions should support future scaling without requiring redesign.

---

# 4. Project Objectives

Develop an enterprise AI platform capable of:

* Local LLM inference
* Knowledge Base (RAG)
* Simpro integration
* Tender analysis
* Bid writing
* Quote generation
* RAMS generation
* Contract generation
* Technical document creation
* AI Sales Agent
* Public Tender Agent
* Customer Intelligence
* Future Multi-Agent Architecture

---

# 5. Core Modules

## Local LLM Platform

Features

* Self-hosted inference
* Docker deployment
* Local APIs
* Multi-model support
* Future multi-agent support

---

## Simpro Integration

Objectives

* Local API integration
* Customer data extraction
* Equipment extraction
* Project analysis
* Reporting
* Document generation

---

## Document Generation

Generate:

* Quotes
* RAMS
* Contracts
* Equipment specifications
* Tender responses
* Technical documentation
* Compliance documentation

Future objective:

Fine-tune local models using company documentation for high-quality bid and contract generation.

---

## Knowledge Base

Target capacity

Approximately 5,000+ documents.

Supported content

* PDF
* Word
* RAMS
* Contracts
* Tender responses
* Drawings
* Equipment specifications
* Certificates
* Templates
* Case studies

Requirements

* Metadata
* Versioning
* Local vector database
* RAG search

---

## AI Sales Agent

Capabilities

* Prospect discovery
* Company research
* Lead qualification
* Lead scoring
* Warm outreach preparation
* CRM-ready summaries

---

## Public Tender Agent

Capabilities

* Monitor public tender portals
* Identify opportunities
* Extract requirements
* Analyse bid fit
* Prioritise tenders
* Prepare supporting documentation

---

## Customer Intelligence

Analyse existing customers to identify

* Industries
* Company size
* Geography
* Technology stack
* Pain points
* Buying triggers
* Decision makers
* Common objections

Generate

* Ideal Customer Profile (ICP)
* Negative ICP
* Sales documentation
* Qualification criteria

---

# 6. Engineering Principles

The platform follows these principles:

* Open Source First
* Self Hosted
* Docker First
* API First
* Infrastructure as Code
* Git Version Controlled
* Modular Architecture
* Production Ready
* Enterprise Quality
* Fully Documented
* Reproducible
* Future Scalable

No cloud AI providers unless explicitly approved.

---

# 7. Development Methodology

Before implementation:

* Design
* Architecture
* Documentation
* Trade-off analysis

Never:

* Skip planning
* Skip documentation
* Jump ahead
* Assume prior knowledge

Always:

* Explain why before how
* Work one sprint at a time
* Wait for confirmation before continuing

---

# 8. Sprint Structure

Every sprint must include:

1. Goal
2. Business value
3. Tasks
4. Implementation
5. Commands
6. Configuration
7. Folder structure
8. Files created
9. Verification
10. Rollback procedure
11. Common issues
12. Documentation updates
13. Git commit
14. Acceptance criteria

---

# 9. Documentation Standards

Maintain Git-ready Markdown documentation.

Required documents include:

* Project Design Document (PDD)
* Architecture
* Architecture Decision Records (ADR)
* Network Design
* Docker
* Security
* Knowledge Base
* Development Standards
* Installation Guide
* Backup Strategy
* Disaster Recovery
* Roadmap
* Change Log

---

# 10. Coding Standards

Python

* PEP8
* Black
* Ruff
* Type Hints
* Docstrings
* Logging
* Environment variables
* Configuration files
* Error handling
* Unit testing where appropriate

---

# 11. Docker Standards

* Every service in Docker
* Docker Compose
* Persistent volumes
* Restart policies
* Minimal host installations

---

# 12. Security Standards

* Nginx Reverse Proxy
* HTTPS
* Firewall
* SSH keys
* .env secrets
* Least privilege
* Minimal exposed ports

---

# 13. Phase 2 – Production RAG Knowledge Base

## Objective

Transform the existing Open WebUI deployment into an enterprise-grade Retrieval-Augmented Generation (RAG) platform.

## Goals

* Replace embedded vector storage with PostgreSQL + PGVector
* Replace default document extraction with Apache Tika
* Use Ollama for local embeddings
* Support enterprise-scale document indexing
* Provide the foundation for all future AI modules

---

## Architecture

```
                    CLIVE Platform

        +-------------------------------+
        |          Open WebUI           |
        |           (RAG UI)            |
        +---------------+---------------+
                        |
        +---------------+---------------+
        |                               |
        v                               v

     Ollama                     PostgreSQL
 llama3.2 + nomic-embed         + PGVector

        ^
        |
        |
 Apache Tika
Document Extraction
```

---

## Data Flow

1. User uploads a document.

2. Open WebUI sends the document to Apache Tika.

3. Apache Tika extracts text.

4. Ollama generates embeddings using `nomic-embed-text`.

5. Embeddings are stored in PostgreSQL + PGVector.

6. User submits a question.

7. PGVector retrieves relevant document chunks.

8. Retrieved context is injected into the LLM prompt.

9. Open WebUI generates the final response.

---

# 14. Phase 2 Project Structure

```text
.
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
├── structure.txt
├── README.md
│
├── configs/
│   └── postgres/
│       └── init-pgvector.sql
│
├── scripts/
│   ├── backup.sh
│   └── verify.sh
│
└── docs/
    ├── architecture.md
    ├── ADR-001-pgvector.md
    ├── ADR-002-tika.md
    ├── configuration.md
    ├── PDD.md
    ├── roadmap.md
    └── CHANGELOG.md```

---

# 15. Long-Term Roadmap

| Phase | Project                        | Outcome                                           |
| ----- | ------------------------------ | ------------------------------------------------- |
| 1     | Foundation                     | Ubuntu, Docker, Ollama, Open WebUI                |
| 2     | Production RAG                 | PGVector, Apache Tika, enterprise document search |
| 3     | Simpro Integration             | API integration, reporting, business data         |
| 4     | Document Generation            | Quotes, RAMS, contracts, technical documentation  |
| 5     | Security & Reverse Proxy       | HTTPS, Nginx, firewall, authentication            |
| 6     | AI Sales Agent                 | Lead discovery, research, qualification           |
| 7     | Public Tender Agent            | Tender monitoring and bid analysis                |
| 8     | Customer Intelligence          | ICP generation and customer analytics             |
| 9     | Multi-Agent Architecture       | Orchestrated AI workflows                         |
| 10    | Monitoring & Disaster Recovery | Backups, health monitoring, recovery              |

---

# 16. End Goal

Deliver a fully self-hosted, enterprise-grade AI platform capable of supporting every stage of the company's operational workflow—from knowledge retrieval and document generation to sales automation, tender management, and intelligent business decision support—while maintaining complete ownership and control of company data.