# CLIVE – Phase 2: Production RAG Infrastructure

## Overview

Phase 2 upgrades the CLIVE AI platform from a basic local LLM environment into a production-ready Retrieval-Augmented Generation (RAG) platform.

The default Open WebUI components were replaced with production-grade services to improve reliability, scalability, and retrieval accuracy while keeping all data local.

---

# Objectives

- Deploy PostgreSQL with PGVector for vector storage
- Deploy Apache Tika for document extraction
- Configure Open WebUI to use PGVector and Tika
- Configure local Ollama embeddings
- Build and verify an end-to-end RAG pipeline
- Improve retrieval performance for technical documentation
- Create an automated backup and restore process

---

# Technology Stack

| Component | Purpose |
|-----------|---------|
| Docker Compose | Multi-container orchestration |
| PostgreSQL 16 | Database |
| PGVector | Vector database extension |
| Apache Tika | Document extraction |
| Ollama | Local embedding and LLM runtime |
| nomic-embed-text | Embedding model |
| Open WebUI | RAG interface |

---

# Project Structure

```
phase2/
│
├── configs/
│   └── postgres/
│       └── init-pgvector.sql
│
├── scripts/
│   ├── verify.sh
│   └── backup.sh
│
├── backups/
│
├── docker-compose.yml
└── .env
```

---

# Step 1 – Deploy Production RAG Services

## Services Deployed

- Ollama
- Open WebUI
- PostgreSQL + PGVector
- Apache Tika

## Configuration

Created a Docker Compose stack containing all four services.

Configured:

- PostgreSQL credentials
- PGVector connection
- Apache Tika
- Local embedding engine
- Hybrid Search

## Verification

Verified:

- All containers running
- PostgreSQL healthy
- PGVector extension installed
- Apache Tika responding
- Ollama API responding
- Open WebUI accessible

Created a `verify.sh` script to automate service health checks.

---

# Security

PostgreSQL and Apache Tika are bound to:

```
127.0.0.1
```

instead of

```
0.0.0.0
```

This restricts access to the local machine only and prevents unnecessary network exposure.

---

# Step 2 – Configure Local Embeddings

Downloaded the embedding model:

```
nomic-embed-text
```

using:

```bash
docker exec clive-ollama ollama pull nomic-embed-text
```

Verified installation with:

```bash
docker exec clive-ollama ollama list
```

---

# Build the Knowledge Base

Created a Knowledge Base in Open WebUI.

Uploaded a PDF document.

During processing:

1. Apache Tika extracted text
2. Ollama generated embeddings
3. PGVector stored vectors
4. Open WebUI indexed the document

---

# End-to-End RAG Test

Asked a question relating to the uploaded document.

The AI successfully retrieved the relevant section and answered using the uploaded document rather than its base model knowledge.

This confirmed the complete RAG pipeline was functioning correctly.

---

# Step 3 – Test with Real Technical Documentation

Uploaded a multi-page technical document.

Asked a question referencing a specific section within the document.

Observed how the retrieval system handled dense technical documentation using default settings.

The system successfully retrieved the required information from Section 21, including the replacement equipment allowance and associated cost.

---

# Step 4 – Improve Retrieval

Enabled (already active):

- Hybrid Search

Adjusted chunking parameters.

| Setting | Default | Updated |
|----------|----------|----------|
| Chunk Size | 1000 | 1500 |
| Chunk Overlap | 100 | 200 |

Reindexed the Knowledge Base.

---

# Why Larger Chunks?

Increasing chunk size preserves more surrounding context.

Increasing overlap ensures information near chunk boundaries appears in adjacent chunks.

These changes improve retrieval accuracy for:

- technical specifications
- model numbers
- section references
- compliance clauses

---

# Hybrid Search

Hybrid Search combines:

- BM25 keyword search
- Vector similarity search
- CrossEncoder reranking

Benefits include:

- better exact keyword matching
- improved semantic understanding
- higher retrieval accuracy
- better performance on technical documents

---

# Backup Automation

Created:

```
scripts/backup.sh
```

The script performs:

- PostgreSQL database dump
- compression
- backup integrity verification
- restore verification
- automatic rotation
- retention management

---

# Backup Verification

The script verifies:

- backup file exists
- backup is not empty
- PGVector extension is included
- restore completes successfully
- temporary restore database contains the vector extension

Only after all verification steps pass is the backup considered valid.

---

# Key Concepts Learned

- Docker Compose orchestration
- Docker volumes
- PGVector vector storage
- Apache Tika document extraction
- Local embedding models
- Semantic search
- Hybrid Search
- Chunk sizing
- Chunk overlap
- Backup verification
- Restore testing
- Container networking
- Local-first AI infrastructure

---

# Outcome

Successfully built a production-ready local RAG platform capable of:

- ingesting PDFs and Office documents
- extracting document text
- generating local embeddings
- storing vectors in PostgreSQL
- performing semantic and keyword retrieval
- providing grounded AI responses with cited sources
- protecting the vector database through automated backups

---

# Next Steps

The next planned enhancement is integrating the existing Open WebUI RAG environment with Simpro via API to enable AI-powered document retrieval from external business applications.