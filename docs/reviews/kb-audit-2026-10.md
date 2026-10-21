# Knowledge base audit — 2026-10

> Historical record as of 2026-10-21, commit b4e2c77. Not maintained.

Course correction W3 (`docs/sprints/course-correction/W3-kb-audit.md`). This
file is public (ADR-017): it holds versions, setting names and values, schema,
counts and pass/fail only. Anything naming a document, file, customer or
person goes to the private store, behind neutral labels. Section 1 needed no
such names, so it has no private companion.

Sections 2–4 are written by W3 T2–T4.

## 1. Current state (W3 T1)

Everything here was read on 2026-10-21. It is read-only: SQLite was opened
with `mode=ro`, and Postgres ran `SELECT`s only. Only schema, counts, setting
values and JSON key names were printed; no document text, file name or
identifier was printed.

### 1.1 Versions and RAG settings

| Item | Value | Source |
|---|---|---|
| Open WebUI | 0.11.0 (build `01f4282f`) | `/app/package.json`, `WEBUI_BUILD_VERSION` in `clive-webui` |
| Open WebUI image tag | `main` (unpinned; container created 2026-10-05) | `docker-compose.yml`, `docker inspect` |
| Postgres / pgvector | 16.14 / 0.8.6 | `show server_version`, `pg_extension` in `clive-postgres` |
| Vector store | `pgvector` | `VECTOR_DB` |
| Extraction | `tika` | `rag.content_extraction_engine`, `CONTENT_EXTRACTION_ENGINE` |
| Embedding | `ollama`, `nomic-embed-text`, batch size 1 | `rag.embedding_*`, `RAG_EMBEDDING_*` |
| Chunk size / overlap | 1500 / 200; text splitter `''` (default); minimum size target 0 | `rag.chunk_*`, `rag.text_splitter` |
| Hybrid search | on; BM25 weight 0.5; enriched texts off | `rag.enable_hybrid_search*`, `rag.hybrid_bm25_weight` |
| Top-k / reranker top-k | 3 / 3; relevance threshold 0 | `rag.top_k*`, `rag.relevance_threshold` |
| Reranking | engine `''`, model `''`; `RAG_RERANKING_MODEL` set but empty | `rag.reranking_*`, container environment |
| Full context / bypass retrieval | off / off | `rag.full_context`, `rag.bypass_embedding_and_retrieval` |
| PDF image extraction | off | `rag.pdf_extract_images` |

Settings are read from Open WebUI's `config` table, which overrides the
environment once saved. 50 other `rag.*`/`file.*` keys were not printed: they
are provider credentials and URLs, templates, or unused engines.

**Discrepancy:** `docs/architecture.md`, `docs/PDDs/PDD-phase2.md` and the
Phase 2 entry in `docs/CHANGELOG.md` say hybrid search includes CrossEncoder
reranking. No reranking model or engine is configured. Whether Open WebUI
0.11.0 reranks with an empty model is not settled here; T2 tests retrieval.
Neither the documents nor the configuration were changed.

### 1.2 Counts

| What | Count |
|---|---|
| Knowledge collections (`knowledge`) | 1 |
| Files (`file`) | 5, all in the knowledge collection, with 5 distinct hashes |
| Folders in the collection (`knowledge_directory`) | 0 |
| Users / groups / group members | 1 / 0 / 0 |
| Access grants (`access_grant`) | 0 |
| Chats / messages / files attached to chats | 12 / 60 / 9 |
| Legacy `document` table | 0 |
| Vector collections in pgvector | 7 |
| Chunks in pgvector (`document_chunk`) | 365 |

### 1.3 How files, chunks and metadata are stored

- **Open WebUI database:** SQLite `webui.db`, mounted from
  `/data/openwebui_data`. `file` holds `filename`, `hash`, `path`, `meta`
  (JSON) and `data` (JSON); `data.content` holds the **full extracted text**
  of each file, alongside its vectors. `knowledge` holds `name`,
  `description`, `meta` and `data`, and `knowledge_file` links files to
  collections. `access_grant` (`resource_type`, `resource_id`,
  `principal_type`, `principal_id`, `permission`) and
  `group`/`group_member` are the access-control tables.
- **Vectors:** one table, `document_chunk` (`id`, `vector`,
  `collection_name`, `text`, `vmetadata` JSONB), in the Phase 2 Postgres.
  Indexes: `ivfflat` cosine (`lists=100`) on `vector`; GIN full-text
  (`simple` configuration) on `text`; B-tree on `collection_name`.
- **Each chunk is stored twice.** Every file has its own collection
  (`file-<file id>`), and the knowledge collection holds a second copy:
  5 per-file collections with 182 chunks, plus the knowledge collection with
  182. The seventh collection matches no file or knowledge ID and holds one
  chunk whose only metadata key is `knowledge_base_id`.
- **No orphans:** every chunk with a `file_id` points at an existing file.
- **Vector width:** the column holds 1536 dimensions. In a sample of 50
  chunks at most 768 are non-zero, the width of `nomic-embed-text`, so the
  vectors are zero-padded to the column width.

### 1.4 Metadata stored today

| Level | Keys (count of rows carrying each) |
|---|---|
| File (`file.meta`) | `name`, `content_type`, `size`, `file_hash`, `collection_name`, `data.knowledge_id`, `data.directory_id` (5 each) |
| File (`file.data`) | `content`, `status` (5 each) |
| Collection (`knowledge.meta`, `.data`) | none |
| Chunk (`vmetadata`) | `name`, `source`, `file_id`, `hash`, `Content-Type`, `created_by`, `embedding_config`, `start_index` (364 each); `knowledge_base_id` (1) |

Against W3's goal:
- **Metadata:** no document type, customer, date or author is stored at any
  level. Only file-system facts and provenance are.
- **Versioning:** no version field. A file's `hash` distinguishes contents;
  nothing links two versions of one document.
- **Access restriction:** the one collection has no access grants, and no
  groups exist.

T2 tests what Open WebUI can do about each.

### 1.5 Commands

Run from the repository root at `b4e2c77`. Output above is trimmed, and
values are shown only for non-secret settings.

```bash
docker inspect clive-webui -f '{{.Config.Image}} created={{.Created}}'
docker exec clive-webui sh -c 'grep -m1 "\"version\"" /app/package.json'
docker exec clive-webui sh -c 'env | cut -d= -f1 | sort'   # names only
# then the values of WEBUI_BUILD_VERSION, VECTOR_DB, CONTENT_EXTRACTION_ENGINE,
# RAG_EMBEDDING_ENGINE, RAG_EMBEDDING_MODEL, RAG_RERANKING_MODEL,
# ENABLE_RAG_HYBRID_SEARCH only
```

- **SQLite, through `docker exec -i clive-webui python3`** (read-only
  connection to `file:/app/backend/data/webui.db?mode=ro`):
  - `count(*)` per table;
  - `pragma table_info` for the file, knowledge, access and config tables;
  - JSON key names of `file.meta`, `file.data`, `knowledge.meta` and
    `knowledge.data`;
  - values of `rag.*`/`file.*` config keys matching tuning names and not
    matching key/secret/password/token/url/auth/header/cookie.
- **Postgres, through `docker exec -i clive-postgres psql -At`** with the
  container's own credentials:
  - `pg_extension`, `information_schema` and `pg_indexes`;
  - `count(*)` and `count(distinct collection_name)` on `document_chunk`;
  - `jsonb_object_keys(vmetadata)` with counts, and `vector_dims` with counts;
  - non-zero components in a 50-row sample.
- **Collections matched to files:** IDs were piped from SQLite into a Postgres
  temporary table and compared there; only counts were printed.
