# ADR-002: Vector Database — PostgreSQL + PGVector

## Status
Accepted (implemented, Phase 2)

## Context
Open WebUI ships with an embedded vector store by default, which is not suitable for CVC's target scale (~5,000+ documents) or for production reliability, backup, and querying needs. A dedicated, self-hosted vector database was required.

## Decision
Use **PostgreSQL with the PGVector extension** (`pgvector/pgvector:0.8.6-pg16` Docker image) as the vector store, configured as Open WebUI's `VECTOR_DB`.

## Alternatives Considered
- **Dedicated vector databases (Milvus, Qdrant, Weaviate, Chroma)** — rejected for this phase: each adds another service to operate, back up, and secure, for a workload (~5,000 documents) that PGVector comfortably handles. PostgreSQL is also already a well-understood, mature piece of infrastructure the team can support long-term.
- **Continuing with Open WebUI's default embedded store** — rejected: not production-grade, no independent backup/restore story, and doesn't scale cleanly to the target document count.

## Consequences
- Positive: a single, mature, well-documented database technology; straightforward backup/restore (`scripts/backup.sh` dumps and verifies it); direct integration with Open WebUI via `PGVECTOR_DB_URL`.
- Positive: keeping the Phase 2 database (`postgres`, port 5432) entirely separate from the later Phase 3 mock database (`simpro-mock-db`, port 5433) means Phase 3 development/testing can never corrupt the production knowledge base.
- Negative: PGVector's approximate nearest-neighbor performance at very large scale (well beyond 5,000 documents) has not been load-tested; if the Knowledge Base grows substantially beyond current projections, this decision should be revisited.
- Bound to `127.0.0.1` only, not `0.0.0.0`, to avoid exposing the database beyond the local host — a deliberate, minimal-exposure choice consistent with the project's security standards.
