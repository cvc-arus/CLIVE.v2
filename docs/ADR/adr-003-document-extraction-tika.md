# ADR-003: Document Extraction — Apache Tika

## Status
Accepted (implemented, Phase 2)

## Context
The Knowledge Base needs to ingest a wide variety of enterprise document formats — PDF, Word, RAMS, contracts, tender responses, drawings, equipment specifications, certificates, templates, case studies — and extract clean text for embedding. Writing and maintaining per-format parsers was not attractive for a single-developer project.

## Decision
Use **Apache Tika** (`apache/tika:3.3.1.0-full` Docker image) as the content-extraction engine, configured as Open WebUI's `CONTENT_EXTRACTION_ENGINE`.

## Alternatives Considered
- **Format-specific Python libraries (e.g. `pypdf`, `python-docx`) wired in manually** — rejected: each new document type (drawings, certificates, etc.) would require its own integration and testing, multiplying maintenance burden.
- **Cloud document-extraction APIs (e.g. AWS Textract, Google Document AI)** — rejected: violates the no-cloud-dependency principle and would send potentially sensitive CVC documents (contracts, RAMS) off-premises.
- **Open WebUI's built-in default extraction** — rejected: less robust across the full range of formats CVC needs, particularly dense technical documents with embedded tables and section references.

## Consequences
- Positive: one extraction service handles the full range of target formats without per-format custom code; runs entirely locally.
- Positive: verified in practice — a multi-page technical document with a specific section reference (Section 21, replacement equipment allowance) was correctly extracted and retrieved end-to-end.
- Negative: Tika is a JVM-based service with its own resource footprint; on the current 32GB/RTX 3080 development host this hasn't been a problem, but it's a consideration for lower-spec deployments.
- Bound to `127.0.0.1` only, matching the same minimal-exposure principle applied to PostgreSQL.
