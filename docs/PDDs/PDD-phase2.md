# Phase 2 Project Design Document — Production RAG Knowledge Base (As-Built)

**Status:** Complete (retrospective PDD — written after implementation, since none existed)
**Source:** `docs/phase2.md`, `docker-compose.yml`, `configs/postgres/init-pgvector.sql`, `scripts/backup.sh`, `scripts/verify.sh`

## 1. Objective

Upgrade the Phase 1 chat environment into a production-grade Retrieval-Augmented Generation platform: replace Open WebUI's embedded vector store and default extraction with dedicated, scalable services, entirely self-hosted.

## 2. Scope

**In scope (delivered):**
- PostgreSQL + PGVector as the vector store
- Apache Tika for document text extraction
- Local Ollama embeddings (`nomic-embed-text`)
- Hybrid Search (BM25 + vector similarity + CrossEncoder reranking)
- Chunking tuning for technical documentation
- Automated backup with restore verification

**Out of scope (deferred):**
- Simpro or other external data sources (Phase 3)
- Document generation (Phase 4)
- Enterprise-scale (5,000+ document) load testing — infrastructure supports it, but it hasn't been exercised at that volume yet

## 3. Architecture (as implemented)

```
Open WebUI ──► Apache Tika (extraction) ──► Ollama (nomic-embed-text) ──► PostgreSQL + PGVector
                                                                              ▲
                                                                    query embeddings
                                                                              │
                                                                        Open WebUI (retrieval)
```

## 4. Key Decisions

| Decision | Choice | Rationale | ADR |
|---|---|---|---|
| Vector database | PostgreSQL + PGVector (`pgvector/pgvector:0.8.6-pg16`) | Self-hosted, mature, integrates directly with Open WebUI, avoids a separate dedicated vector-DB service | `docs/ADR/adr-002-vector-database-pgvector.md` |
| Document extraction | Apache Tika (`apache/tika:3.3.1.0-full`) | Handles PDF, Word, and other enterprise document formats without per-format custom parsers | `docs/ADR/adr-003-document-extraction-tika.md` |
| Embedding model | `nomic-embed-text` via Ollama | Fully local, no cloud dependency, already integrated with the Phase 1 Ollama service | `docs/ADR/adr-002-vector-database-pgvector.md` |
| Chunk size / overlap | 1500 / 200 (up from Open WebUI defaults of 1000 / 100) | Preserves more surrounding context for technical specs, model numbers, and compliance clauses | — |
| Network exposure | Postgres and Tika bound to `127.0.0.1` only | Prevents unnecessary exposure beyond the local host | — |

## 5. Configuration (as implemented)

`docker-compose.yml` (relevant excerpt):

```yaml
postgres:
  image: pgvector/pgvector:0.8.6-pg16
  ports: ["127.0.0.1:5432:5432"]
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]

tika:
  image: apache/tika:3.3.1.0-full
  ports: ["127.0.0.1:9998:9998"]

open-webui:
  environment:
    - VECTOR_DB=pgvector
    - PGVECTOR_DB_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
    - CONTENT_EXTRACTION_ENGINE=tika
    - TIKA_SERVER_URL=http://tika:9998
    - RAG_EMBEDDING_ENGINE=ollama
    - RAG_EMBEDDING_MODEL=nomic-embed-text
    - ENABLE_RAG_HYBRID_SEARCH=true
```

## 6. Data Flow

1. User uploads a document to Open WebUI.
2. Open WebUI sends it to Apache Tika for text extraction.
3. Ollama generates embeddings (`nomic-embed-text`).
4. Embeddings are stored in PostgreSQL + PGVector.
5. On a query, PGVector retrieves relevant chunks; Hybrid Search combines BM25 keyword matching with vector similarity and CrossEncoder reranking.
6. Retrieved context is injected into the LLM prompt; Open WebUI generates the grounded response.

## 7. Verification

- `./scripts/verify.sh` — confirms all containers running, Postgres healthy, PGVector extension installed, Tika responding, Ollama responding, Open WebUI accessible
- End-to-end test: uploaded a multi-page technical document, asked a question referencing a specific section, confirmed the system retrieved the correct section (including a specific cost figure) rather than answering from base model knowledge

## 8. Backup Strategy

`scripts/backup.sh` performs: PostgreSQL dump → gzip compression → integrity verification → temporary-database restore verification (confirms the PGVector extension is present in the restored copy) → rotation/retention. A backup is only considered valid once every step passes. See `backups/clive_pgvector_20260805_160501.sql.gz` for the most recent artifact at time of writing.

## 9. Outcome

A working, fully local RAG pipeline capable of ingesting PDFs/Office documents, extracting text, generating embeddings, storing vectors, and answering questions with retrieval grounded in uploaded documents — verified end-to-end, with automated, verified backups.

## 10. Follow-on Work Identified at the Time

Integrating this RAG environment with Simpro via API, so AI-powered retrieval can draw on live business data as well as uploaded documents — this became Phase 3.
