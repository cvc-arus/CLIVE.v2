# Knowledge base audit — 2026-10

> Historical record as of 2026-10-21, commit b4e2c77. Not maintained.

Course correction W3 (`docs/sprints/course-correction/W3-kb-audit.md`). This
file is public (ADR-017): it holds versions, setting names and values, schema,
counts and pass/fail only. Anything naming a document, file, customer or
person goes to the private store, behind neutral labels. Section 1 needed no
such names, so it has no private companion.

Section 2 was added on 2026-10-23 at commit 3966eb7 (W3 T2). Section 3 was
added on 2026-11-05 at commit 0a4b630 (W3 T3). Section 4 was added on
2026-11-05 at commit 9200219 (W3 T4).

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

### 2.8 Re-run on Open WebUI 0.12.3 (2026-10-23)

Run after the upgrade to the pinned release v0.12.3 (ADR-018), at commit
10e2994, with the same synthetic documents and set-up. Two changes to the
method:
- **Path B:** a third synthetic text with a unique code word (`S1 v3`) was
  written over v1's file, so the duplicate-content check could not confound it.
- **Nested groups:** a probe for the nested groups added in 0.12.0.

| Requirement | 0.11.0 (§2.2–§2.5) | 0.12.3 |
|---|---|---|
| Metadata | Partly met: fields on the file only | **Partly met, closer:** fields on the file **and on every chunk**; still no filter in the retrieval API or in chat |
| Versioning | Not met | **Not met:** in-place replacement now works cleanly, but no history is kept |
| Access restriction | Met | **Met**, including inheritance through nested groups |
| Deletion | Met | **Met** |

**Metadata.** The four custom fields (`doc_type`, `customer`, `doc_date`,
`author`) now appear in every chunk's `vmetadata`, next to `content_type`,
`file_hash` and `size`. The pgvector client's `search()` accepts a metadata
`filter`, but Open WebUI calls it only internally (by `hash` and `file_id`).
`QueryCollectionsForm` is unchanged, so neither the API nor chat can limit
retrieval to a type, customer or date. Exposing that filter is now a small
extension, not a new store.

**Versioning.**
- **Path A** (v2 as a second file): unchanged. Both versions are retrievable
  and unlinked.
- **Path B, confounded as in §2.3:** with v2's separate file present, the
  content update returned **500**. The log shows the same "Duplicate content
  detected" error, now unhandled.
- **Path B with `S1 v3`:** the content update and the collection re-index
  both returned 200. The file's chunks in both copies hold only v3's text
  (2 chunks with v3's code word, 0 with v2's), and collection search finds
  v3. Replacement in place works, but the old version is gone.

**Access, as the test user.**

| Situation | Search collection | Search per-file copy | Chat answer |
|---|---|---|---|
| No grants / group grant, user outside | 403 / 403 | 403 / 403 | code word absent; 0 sources |
| User in the granted group (control) | 200, found | 200, found | code word in answer; 1 source |
| User only in a child group of the granted group | 200, found | 200, found | code word in answer; 1 source |
| User removed again | 403 | 403 | code word absent; 0 sources |

The admin-only rule for models with no `model` row is unchanged in 0.12.3, so
the chat test again needed the scratch model and a temporary
`llama3.2:latest` row.

**Deletion.** Removing each file from the collection left 0 chunks in both
copies and deleted the file record.

**After clean-up:**
- pgvector: 365 chunks in 7 collections; `knowledge-bases` has 1 entry.
- SQLite: files / collections / links 5 / 1 / 5; models, grants, groups and
  group members 0.
- The new `model_history` table is empty.

## 3. Extraction spot-check (W3 T3)

Run 2026-11-05 against Tika 3.3.1 (`apache/tika:3.3.1.0-full`) with
`scripts/extraction_spotcheck.py` at commit `0a4b630`. Alex chose the ten
files and ran the script. It makes the same `PUT /tika/text` call Open WebUI
0.12.3 makes, then calls `PUT /tika/html` to get the page structure.

The files are named here only by label and type. The label-to-file mapping
and the extracted text are in the private store
(`docs/simpro/private/kb-extraction/2026-11-05/`, ADR-017). For this run only,
Alex let Claude Code open the source folder for the fact check in §3.2.
Claude Code did not read the private text files.

### 3.1 Per file

Figures come from `metrics.json`. A page counts as empty when it has fewer
than 20 non-whitespace characters. For DOCX files, the page count is Word's own
count from the file's metadata.

| Label | Type | Pages | Chars/page | Empty pages | Tables / rows | Headings | OCR | Result |
|---|---|---|---|---|---|---|---|---|
| F1 | Product datasheet, PDF | 5 | 2,040 | 0 | 0 / 0 | 0 | no | Text layer complete |
| F2 | Product datasheet, PDF | 1 | 2,132 | 0 | 0 / 0 | 0 | no | Text complete; spec table flattened to `label (unit) value` lines |
| F3 | Customer proposal, PDF | 15 | 1,584 | 0 | 0 / 0 | 0 | no | Text layer complete |
| F4 | Supplier registration record, PDF | 2 | 1,145 | 0 | 0 / 0 | 0 | no | Text layer complete |
| F5 | Photographed invoice, JPEG | — | 1,366 chars | — | 0 / 0 | 0 | yes | Printed text read with some character errors; handwritten note largely lost |
| F6 | Company policy, PDF | 14 | 1,974 | 0 | 0 / 0 | 0 | no | Text layer complete |
| F7 | Combined datasheet pack, PDF | 49 | 1,387 | 0 | 0 / 0 | 0 | no | Text layer complete |
| F8 | Tender response, DOCX | 40 | 1,380 | — | 34 / 149 | 16 | no | Tables and headings kept |
| F9 | Technical submission, DOCX | 17 | 2,114 | — | 1 / 104 | 0 | no | Parts table kept as one table |
| F10 | Equipment model schedule, DOCX | 3 | 908 | — | 4 / 34 | 16 | no | Tables and headings kept |

All ten files extracted without errors or Tika warnings, in at most 4.4 s each.

### 3.2 Fact check against the W4 question set

Alex's W4 evaluation set has 40 questions. It is git-ignored, and its questions
are not reproduced here. Each question has must-include facts and the
documents that hold them. A scratch check, not tracked, re-extracted each source
file in memory the way Open WebUI does. It then looked for every fact in the
text of the question's documents, after lowercasing and removing whitespace and
thousands separators. The check printed only question IDs and pass/fail.

The first run failed five more questions, but the fault was in the checker,
not in extraction. It did not map `&` in a file name to `_` the way the
question set's source names do, and it did not remove thousands separators.
Both were fixed before the run below.

| Category | Questions | All facts in the extracted text | Missing |
|---|---|---|---|
| lookup | 24 | 22 | 2 |
| multi_doc | 10 | 9 | 1 |
| not_found | 6 | — (no facts to find) | — |

Of the three misses, only one is a real extraction gap:

- **One lookup: real gap.** A handwritten note on the photographed invoice
  (F5) is not read by OCR. The amount is lost; one word survives.
- **One lookup and one multi_doc: the facts are in the text.** F2's spec table
  comes out as `label (unit) value`, so the unit sits before the number.
  A model can read it, but the question set's exact `value+unit` patterns do
  not match. This is a fix to the question set, not an extraction gap.

So 33 of the 34 facts that should be answerable are present in what Open WebUI
would index. 4 of the 6 `not_found` questions have distractor values present in
the corpus, which makes them a real test of hallucination.

### 3.3 Findings

- **PDF tables and headings are not kept.** Tika's PDF parser emits no table
  or heading markup, so the spec tables in F1, F2 and F7 become plain lines.
  The values survive, but row and column structure is lost before chunking.
  DOCX tables and headings are kept.
- **OCR works on printed text, not handwriting.** F5 (JPEG) went through
  Tesseract. Its printed fields were read with some errors, and the handwriting
  was not. No PDF needed OCR: every PDF page had a text layer.
- **Two of the task's file types were not in the sample:** a scanned PDF
  certificate and a drawing. OCR on scanned PDFs, and drawings, are therefore
  untested.

### 3.4 Commands

```bash
# Alex, 2026-11-05 (input folder outside the repository)
uv run python scripts/extraction_spotcheck.py <folder>
# Claude Code: per-file figures from
# docs/simpro/private/kb-extraction/2026-11-05/metrics.json
# Claude Code: fact check (scratch script, not tracked; prints IDs and pass/fail)
uv run --with pyyaml==6.0.2 python answerability.py evaluation/eval-set.yaml <folder>
```

Fact check summary output (after the two checker fixes in §3.2):

```text
lookup     FAIL 2
lookup     PASS 22
multi_doc  FAIL 1
multi_doc  PASS 9
```

## 4. Gap report and options (W3 T4)

Written 2026-11-05 against Open WebUI 0.12.3. The requirements come from the
scope documents:
- `docs/scope/master-project-document.md`, Knowledge Base: metadata,
  versioning, a local vector database and RAG search, for about 5,000
  documents of the types listed.
- `docs/scope/clive-scope.md`: "Every document must support metadata",
  "Every document must support future versioning".
- The W3 goal: access restriction for sensitive documents.

Before writing, the read-only counts were re-checked at `9200219`. They match
§2.7: 1 collection, 5 files, 365 chunks in 7 collections, and 0 groups,
access grants and model rows. No scratch item is left from T2.

### 4.1 Requirements against findings

| Requirement | Result | Evidence | What is missing |
|---|---|---|---|
| Metadata on every document | **Partly met** | §2.8: custom fields set at upload reach the file record and every chunk | Retrieval cannot filter on them: no filter in the retrieval API or in chat. Nothing sets the fields today, since manual uploads carry none (§1.4) |
| Future versioning | **Partly met** | §2.3, §2.8: a content update replaces a file in place, and two uploads coexist unlinked | No version history and no "current version by default". "Future" versioning only needs a stable document identity and version field from the first ingestion, so it can be added later without re-ingesting |
| Access restriction for sensitive documents | **Met, not usable yet** | §2.4, §2.8: group grants hold in search and chat, including nested groups | No model rows exist, so regular users cannot chat at all (§2.4; still 0 rows on 2026-11-05). Groups and grants are not set up |
| Deletion (W3 T2) | **Met** | §2.5, §2.8 | — |
| Local vector database | **Met** | §1.1: pgvector 0.8.6 in the Phase 2 Postgres (ADR-002) | Not load-tested at about 5,000 documents (ADR-002, PDD-phase2). Each chunk is stored twice and padded to 1536 dimensions (§1.3), so vector storage is about four times the minimum |
| RAG search | **Met, below documented quality** | §1.1, §3.2: hybrid search works; 33 of 34 answerable facts in the W4 set survive extraction | No reranker is configured, although three documents say CrossEncoder reranking is used (§1.1). Top-k is 3 |
| Document types: PDF, Word | **Met** | §3.1 | PDF tables and headings are flattened to plain lines; DOCX keeps them |
| Document types: certificates (scans), drawings | **Unknown** | §3.3 | No scanned PDF and no drawing in the T3 sample. OCR fails on handwriting |

### 4.2 Options

| Option | What it means | Effort (rough) | Risk |
|---|---|---|---|
| **A. Keep** as is | Bulk-upload through the Open WebUI interface | None | **High.** About 5,000 documents with no metadata and no document identity: adding either later means re-ingesting everything, the cost W3 exists to avoid. Regular users still cannot chat |
| **B. Extend: ingestion conventions** (no new service) | A CLIVE ingestion script calls Open WebUI's own API (the calls tested in §2). Each upload sets the metadata fields plus `doc_id` and `version`. Collections are split by document family and sensitivity, each granted to groups, so the choice of collection acts as the filter. A superseded version moves to an admin-only archive collection, so the current version is the default and old versions stay retrievable on purpose. Model rows and groups are created so regular users can chat | 3–5 days, plus Alex's time on the field list and collection layout | **Medium-low.** Relies on Open WebUI's API, which changed behaviour between 0.11 and 0.12 (§2.8: a 400 became a 500); the image is pinned (ADR-018), and the script's checks re-run on each upgrade. Retrieval still cannot filter on metadata within a collection |
| **B+. Extend: patch Open WebUI** to expose the metadata filter | A local change to `QueryCollectionsForm` and the chat path. The pgvector client already accepts a filter (§2.8) | 2–4 days, then re-applied on every upgrade | **High.** A fork to maintain; it breaks the pinned-release model of ADR-018 |
| **C. Own the pipeline** | A CLIVE ingestion service writes chunks and metadata to pgvector, and a retrieval tool, like the planned `clive-gateway`, serves filtered, versioned search. Open WebUI stays the front end | 3–6 weeks; needs an ADR (new service, persistence strategy) | **Medium.** Full control of metadata filters, versions and table-aware chunking, but it duplicates what Open WebUI does today, adds a service to secure and back up, and competes with Phase 3B for the same effort |
| **D. Extraction improvements** (alongside any option) | (1) Test scanned PDFs and drawings before bulk ingestion. (2) If tables matter, which the W4 evaluation can show, try a table-aware extraction engine; Open WebUI supports Docling, which would be a new container. (3) Treat handwriting and drawings as metadata-only unless tests show otherwise | (1) under a day; (2) 2–3 days to evaluate; it needs an ADR to adopt | **Low** for (1). (2) adds a service. The 1 handwriting miss in §3.2 shows OCR's limit, not a pipeline fault |

Also needed under every option, and small: configure a reranker or correct the
three documents that claim one (§1.1), and decide whether the duplicate chunk
copies and 1536-dimension padding matter at 5,000 documents.

### 4.3 Recommendation (non-binding)

**Option B, with D(1) first; C only if evidence calls for it.**

- B meets the scope as written: metadata on every document, and the
  `doc_id`/`version` fields that make future versioning possible without
  re-ingesting. It also makes access restriction usable, with no new service,
  store or dependency.
- The one gap B leaves is metadata filtering within a collection. The W4
  evaluation is the right place to measure whether that gap costs answer
  quality. If it does, C becomes the next step and needs its own ADR.
- B+ is not recommended, because of the fork it creates.

**No ADR is drafted.** B uses Open WebUI's existing API and adds no service,
store, dependency category or architectural change (root `CLAUDE.md` §3).
Its conventions (fields, collection layout, version rule) belong in the
ingestion task's plan. C, or adopting Docling, would each need an ADR.

**Bulk ingestion: keep it paused** until all of these are done:
1. Alex approves B's field list and collection layout.
2. The ingestion script is built and tested on synthetic documents.
3. Model rows and groups exist, so a regular user can chat with a granted
   collection.
4. Scanned PDFs and drawings have been spot-checked (D1).

The W4 baseline should run on the knowledge base as it will be (after items
1–3), not on today's five unlabelled files.

This is Alex's decision. The outcome goes to `docs/STATUS.md`, and to an ADR
if C or Docling is chosen.
