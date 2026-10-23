# Knowledge base audit — 2026-10

> Historical record as of 2026-10-21, commit b4e2c77. Not maintained.

Course correction W3 (`docs/sprints/course-correction/W3-kb-audit.md`). This
file is public (ADR-017): it holds versions, setting names and values, schema,
counts and pass/fail only. Anything naming a document, file, customer or
person goes to the private store, behind neutral labels. Section 1 needed no
such names, so it has no private companion.

Section 2 was added on 2026-10-23 at commit 3966eb7 (W3 T2). Sections 3–4 are
written by W3 T3–T4.

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

## 2. Requirement tests (W3 T2)

Run on 2026-10-22 and 2026-10-23 against Open WebUI 0.11.0 (the version in
§1.1), through its HTTP API, in a scratch collection deleted afterwards. The
test documents were two short synthetic texts written for the test, `S1 v1`
and `S1 v2`, each holding a unique code word. No real document was used.

| Requirement | Result |
|---|---|
| Metadata: custom fields, and retrieval filtered on them | **Partly met**: fields are stored, but retrieval cannot filter on them |
| Versioning: v1 kept, v2 the default, v1 retrievable on purpose | **Not met** |
| Access restriction: a collection limited to a group | **Met**, in search and in chat answers |
| Deletion: chunks removed from pgvector | **Met** |

### 2.1 Set-up

- An admin API key (`OPENWEBUI_TEST_API_KEY`) and a regular test user
  (`OPENWEBUI_TEST_USER_EMAIL`, `OPENWEBUI_TEST_USER_PASSWORD`), all in `.env`,
  created by Alex. Admins bypass every access check, so access was tested as
  the test user only.
- The scratch items, each recorded and deleted at the end:
  - the collection `w3-t2-scratch`;
  - the group `w3-t2-scratch-group`;
  - the workspace model `w3-t2-scratch-model`;
  - a temporary access row for `llama3.2:latest` (§2.4).
- Each check read three levels: the API response, the SQLite record and the
  pgvector chunks. Output was status codes, counts and booleans only.

### 2.2 Metadata: partly met

`S1 v1` was uploaded with four custom fields (document type, customer, date,
author; synthetic values) in the upload's `metadata` form field.

| Check | Result |
|---|---|
| Fields on the file record (`file.meta.data`) | all four stored |
| Fields on the chunks (`vmetadata`) | none: `created_by`, `embedding_config`, `file_id`, `hash`, `name`, `source`, `start_index` only |
| A filter in the retrieval API | none: `QueryCollectionsForm` takes `collection_names`, `query`, `k`, `k_reranker`, `r`, `hybrid`, `hybrid_bm25_weight`, `enable_enriched_texts` |
| Search for v1's code word | found |

Search runs on chunks, and Open WebUI copies a fixed set of keys onto them,
so custom fields stay one level away from where retrieval looks.

### 2.3 Versioning: not met

| Path | What was done | Result |
|---|---|---|
| A: v2 as a second file | `S1 v2` added next to `S1 v1` | Both versions retrievable side by side; the hashes differ, and nothing links the two files |
| B: v2 over v1 | v1's text replaced (`POST /api/v1/files/{id}/data/content/update`), then the collection re-indexed (`POST /api/v1/knowledge/{id}/file/update`) | v1's text gone everywhere (0 chunks), so no history. The file also dropped out of the collection: the re-index returned **400** "Duplicate content detected", because path A's file held identical text |

Path B's outcome is confounded by path A's file. Neither path gives "v2 by
default, v1 on request".

### 2.4 Access restriction: met

The collection (holding `S1 v2`) was checked as the test user in four
situations; the third is the control.

| Situation | Listed | Search collection | Search per-file copy | Read file | Chat answer with the collection attached |
|---|---|---|---|---|---|
| No access grants | no | 403 | 403 | 404 | not run |
| Read grant to a group, test user outside | no | 403 | 403 | 404 | 200; code word absent; 0 sources |
| Test user added to the group (control) | yes | 200, found | 200, found | 200 | 200; code word in answer; 1 source |
| Test user removed again | no | 403 | 403 | 404 | 200; code word absent; 0 sources |

**Regular users cannot chat as configured.** The first chat attempt returned
400 "Model not found":
- A model with no row in the `model` table is admin-only.
- A workspace model also needs read access on its base model
  (`has_base_model_access` in `utils/access_control/__init__.py`).
- §1 counted 0 model rows, so no regular user can use any model today.

The chat test therefore used:
- a scratch workspace model on `llama3.2:latest`, shared with the test user;
- a temporary `llama3.2:latest` row granting the test user read access.

Both were deleted afterwards.

### 2.5 Deletion: met

| File | Chunks before | After `POST /api/v1/knowledge/{id}/file/remove` | File record |
|---|---|---|---|
| `S1 v1` | 1 (its collection copy was already gone, §2.3) | 0 | gone |
| `S1 v2` | 2 (per-file and collection copies) | 0 | gone |

In this version, removing a file from a collection deletes the file record
too: a later `DELETE /api/v1/files/{id}` returned 404. The full text in
SQLite went with it, and the file count returned to 5.

### 2.6 The `knowledge-bases` collection

§1.3's seventh, unmatched collection is `knowledge-bases`, Open WebUI's index
of collection names and descriptions. The code calls it a "system
meta-collection" and never lets a non-admin search it. Its entry count went
from 1 to 2 while the scratch collection existed, and back to 1 afterwards.

### 2.7 State after clean-up

Every scratch item was deleted. The read-only counts from §1 match:

| What | §1 | After clean-up |
|---|---|---|
| pgvector chunks / collections | 365 / 7 | 365 / 7 |
| `knowledge-bases` entries | 1 | 1 |
| Files / knowledge collections / links | 5 / 1 / 5 | 5 / 1 / 5 |
| Models / access grants / groups | 0 / 0 / 0 | 0 / 0 / 0 |
| Users | 1 | 3 |

The users now are:
- the original admin;
- a second admin, created 2026-10-22, not by this test;
- the test user, Alex's, kept for now.

The API key also remains.
