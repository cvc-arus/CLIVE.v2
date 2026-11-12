# Knowledge base ingestion (W3 option B)

> **Full template**: this changes data (the knowledge base, its collections and
> metadata) and security (groups and access grants in Open WebUI).

| | |
|---|---|
| **Status** | Approved (Alex, 2026-11-11) |
| **Depends on** | W3 decision (option B, Alex 2026-11-05; `docs/reviews/kb-audit-2026-10.md` §4); W4 T3 runner (`scripts/eval/run_eval.py`) |
| **Related ADRs** | ADR-002 (pgvector), ADR-003 (Tika), ADR-017 (private store), ADR-018 (pinned images). No new ADR: option B uses Open WebUI's existing API and adds no service, store or dependency category (W3 §4.3). Adopting Docling, or option C, would each need one |

## 1. Goal

Make the knowledge base ready for bulk ingestion by meeting option B's four
conditions (`docs/STATUS.md`, W3 row):

1. Alex approves the field list and collection layout (§4.1–§4.4).
2. An ingestion script is built and tested on synthetic documents.
3. Model rows and groups exist, so a regular user can chat with a granted
   collection.
4. Scanned PDFs and drawings are spot-checked (D1).

Also, from the W4 T3 dry run (2026-11-06): configure a reranker and remove
duplicated content, because retrieval did not return the chunks holding the
expected facts. At the end, the current 9 files are re-ingested under the
new conventions and the W4 T4 baseline can run.

Out of scope: bulk ingestion of the ~5,000 documents (Alex starts it after
this sprint), metadata filtering inside a collection (option B+ or C),
Docling (D2), and the duplicate chunk copies and 1536-dimension padding
(W3 §1.3; revisit at volume).

## 2. Business value

- Every document gets a stable identity, a version and metadata from its
  first upload, so versioning and filtering can be added later without
  re-ingesting 5,000 documents (W3 §4.1).
- Commercial and restricted documents become visible only to the groups that
  should see them, and regular staff can use CLIVE at all (today only admins
  can, W3 §2.4).
- Answers improve where the dry run showed them failing: the right chunk
  reaches the model.

## 3. Tasks

### T1 [HUMAN] Field list and collection layout (condition 1)
Alex confirms or amends §4.1 (fields), §4.2 (collections), §4.3 (groups) and
§4.4 (version rule). Claude Code then records the result in this file.
**Stop point:** §4.1–§4.4 marked "Approved by Alex <date>".

### T2 API probe on synthetic documents
Settle the open behaviours below on Open WebUI v0.12.3, in scratch items
deleted afterwards, as W3 T2 did (synthetic texts with code words; output is
status codes, counts and booleans only):
1. **Archiving a version.** Can a file be linked to two collections, and does
   removing it from one keep the file record (in W3 §2.5 removal deleted the
   record; a file linked to a second collection was not tested)? If not, the
   archive copy is a fresh upload of the old source.
2. **Changing metadata** of an existing file without re-uploading
   (`status: superseded`), and whether chunks pick it up.
3. **Knowledge attached to a workspace model.** With the model's collections
   attached and no `files` in the request, does retrieval run over the API,
   and does it respect a regular user's group grants? The chat path depends
   on the model's function-calling mode (`utils/middleware.py`: `legacy`
   attaches the files, native exposes knowledge as a tool).
4. **Identical content** in two uploads: the 400/500 "Duplicate content
   detected" error (W3 §2.3, §2.8), so the script can report it cleanly.

**Stop point:** a results table in this file (§4.5); §4.4's mechanism fixed.

### T3 Ingestion script and offline tests
`scripts/kb/ingest.py` (§4.6), with `tests/test_kb_ingest.py` (respx, invented
content). Manifest and layout formats with tracked examples; private paths
git-ignored, backed up and denied to Claude Code (§6).
**Stop point:** offline suite and lint pass; `check` validates the example
manifest.

### T4 Live test on synthetic documents (condition 2)
Run `setup`, `plan`, `apply` and `verify` against Open WebUI with a synthetic
manifest in scratch collections (prefix `scratch-`): first upload, unchanged
re-run (no changes), a new version (old one archived, new one the default),
deletion, a commercial document hidden from the test user. Clean up: the
scratch collections are deleted by the test session's own API calls, as in
W3 T2, not by `ingest.py` (§4.6).
**Stop point:** every check passes; scratch items deleted; counts back to the
start.

### T5 Groups, collections and the CLIVE model (condition 3)
1. **[HUMAN]** Alex creates the groups in §4.3 and adds people to them in the
   Admin Panel (people's names never reach Claude Code).
2. `ingest.py setup` creates the collections in §4.2 and their grants.
3. **[HUMAN]** Alex creates the workspace model `clive` (§4.7) in the Admin
   Panel, and gives its base model a model row with read access for `staff`
   (W3 §2.4: a workspace model also needs read access on its base model).
4. Verify as the test user (`OPENWEBUI_TEST_USER_*`): the model is usable,
   granted collections answer, the others do not.

**Stop point:** the access table in §9 passes for the test user.

### T6 [HUMAN] Scanned PDFs and drawings spot-check (D1, condition 4)
Alex picks a few scanned certificates and drawings and runs
`uv run python scripts/extraction_spotcheck.py <folder>`. Claude Code reads
only `metrics.json` and reports chars per page, empty pages and OCR use.
Decision per type: index the text, or index metadata only (W3 §4.2 D3).
**Stop point:** decision recorded as a note under §4.1's table.

### T7 Retrieval settings: reranker and top-k
Configure a local reranker in Open WebUI (Admin Panel → Settings → Documents)
and set top-k and reranker top-k (§4.8). Measure with the W4 runner on the
current collection before and after (same question ids, results git-ignored,
counts only). Correct the three documents that claim CrossEncoder reranking
(W3 §1.1) once it is true.
**Stop point:** before/after counts reported; Alex keeps or reverts.

### T8 Re-ingest the current files
1. **[HUMAN]** Alex writes `kb/manifest.yaml` for the current files, leaving
   out the combined datasheet pack whose content repeats the single
   datasheets (§4.1, `skip` rule).
2. Run `backup.sh` first, then `plan` and `apply`; `verify`.
3. Point the evaluation at the `clive` model: `EVAL_KNOWLEDGE_ID` becomes
   optional (§4.7) and the runner sends no `files` when it is empty.
4. Dry run on L01, M01, N01; then, **only with Alex's approval**, delete the
   old single collection.

**Stop point:** dry run reported; old collection removed or kept by Alex.

### T9 Close-out
Documentation (§12); W4 T4 and bulk ingestion are unblocked in `STATUS.md`.

## 4. Implementation

Why option B: it meets the scope's metadata and future-versioning
requirements and makes access control usable without a new service (W3 §4.3).
The collection is the filter, because retrieval cannot filter on metadata
inside a collection (W3 §2.8).

### 4.1 Fields (Approved by Alex 2026-11-10)

Set on every upload as file metadata; Open WebUI 0.12.3 copies them onto every
chunk (W3 §2.8). No person's name is stored: ownership is a team.

| Field | Set by | Required | Values |
|---|---|---|---|
| `doc_id` | manifest | yes | Stable identity. The document's own reference when it has one (e.g. a policy code), otherwise `<family>-<nnnn>` |
| `version` | manifest | yes | The document's own revision as text (`A`, `3`, `2024-03`) |
| `title` | manifest | yes | Short title |
| `doc_type` | manifest | yes | `datasheet`, `manual`, `rams`, `method_statement`, `policy`, `certificate`, `drawing`, `technical_submission`, `o_and_m`, `tender_response`, `proposal`, `quote`, `contract`, `template`, `case_study`, `financial`, `hr`, `other` |
| `collection` | manifest | yes | One of §4.2; must match `doc_type`'s allowed collections |
| `customer` | manifest | when for one customer | Customer name as in Simpro |
| `site` | manifest | no | Site name as in Simpro |
| `manufacturer`, `product` | manifest | datasheets, manuals | Free text |
| `doc_date` | manifest | if known | ISO date |
| `owner_team` | manifest | yes | A group from §4.3 |
| `skip` | manifest | no | Reason not to ingest, e.g. `duplicate-of <doc_id>` |
| `status` | script | — | Always `current`, written at upload. It cannot be changed afterwards (§4.5, probe 2), so a file in `kb-archive` is superseded whatever this field says (§4.4) |
| `source_sha256` | script | — | Hash of the source file |
| `ingested_at` | script | — | UTC timestamp |

### 4.2 Collections (Approved by Alex 2026-11-10)

| Collection | Holds (`doc_type`) | Read access |
|---|---|---|
| `kb-products` | datasheet, manual, product certificates | `staff` |
| `kb-hseq` | rams, method_statement, policy, company certificates | `staff` |
| `kb-templates` | template, case_study | `staff` |
| `kb-projects` | technical_submission, drawing, o_and_m | `projects`, `service`, `sales`, `management` |
| `kb-commercial` | tender_response, proposal, quote, contract | `sales`, `management` |
| `kb-restricted` | financial, hr | `management` |
| `kb-archive` | superseded versions of any type | admins only (no grants) |

- `certificate` is allowed in both `kb-products` and `kb-hseq`.
- `other` is allowed in any collection except `kb-archive`; the manifest's
  `collection` field decides.
- The manifest is written by hand and is never generated from a Simpro
  export, so no Simpro record is copied into the knowledge base (ADR-015).
- Write access: admins only. Collection names and descriptions hold no client
  data.

### 4.3 Groups (Approved by Alex 2026-11-10)

`staff` is the parent; `sales`, `service`, `projects`, `hseq` and
`management` are its children, so a grant to `staff` reaches every team
(nested groups work in 0.12.3, W3 §2.8). Teams follow the W2 survey's teams.
Memberships are Alex's, in the Admin Panel.

### 4.4 Version rule (Approved by Alex 2026-11-10; mechanism fixed by T2, Alex 2026-11-11)

- A manifest entry whose `doc_id` exists with another `version` is a new
  version. It is uploaded to its collection with `status: current`.
- The old version is relinked to `kb-archive`: its file is added to
  `kb-archive`, then removed from its collection with `delete_file=false`
  (§4.5, probe 1). Nothing is uploaded or embedded again, and the old source
  file is not needed. The current version is the default and old ones stay
  retrievable on purpose by admins.
- A file's metadata cannot be changed after upload (§4.5, probe 2), so an
  archived file keeps `status: current`. Being in `kb-archive` is what makes
  a file superseded; the version that replaced it is the file with the same
  `doc_id` outside the archive. No `superseded_by` field is stored.
- A file linked to two collections is never removed with the default
  `delete_file`: that deletes the file record and leaves its chunks
  searchable in the other collection (§4.5, probe 1).
- The same `doc_id` and `version` with a different file hash is an error, not
  an update: a changed document needs a new version.
- Nothing is deleted except on an explicit `--delete <doc_id>`.

### 4.5 T2 results

Run by Alex on 2026-11-11 against Open WebUI v0.12.3, with scratch items and
invented texts only. The four counts (collections, groups, files, models)
matched before and after probes 1, 2 and 4. Probe 3's scratch items were
removed afterwards (Alex, 2026-11-11).

| # | What was done | Result |
|---|---|---|
| 1 | One file added to two collections, then removed from the first. Run twice: default removal, then `delete_file=false` | Both adds: 200. Default removal: 200, file record deleted, second collection lists 0 files, **search in the second collection still finds the code word**. `delete_file=false`: 200, file record kept, second collection lists 1 file and search finds the code word; the first collection lists 0 and finds nothing |
| 2 | A file uploaded with `doc_id`, `version`, `status`; then renamed, re-processed (`file/update`), and three guessed metadata routes tried | Rename and re-process: 200, labels unchanged. Guessed routes: 405. Chunk metadata carries the three labels. **No way to change metadata without a new upload** |
| 3 | A scratch workspace model with one collection attached, no `files` in the request. Chat as the test user (not an admin), inside and outside the group granted read on the collection, in default and legacy function-calling mode | Legacy, inside: 200, code word in the answer, 1 source item. Legacy, outside: 200, code word absent, 0 source items, empty answer. Default mode, inside and outside: 200, empty answer, 0 source items. Direct search as the user: 200 and found inside the group, 403 outside |
| 4 | The same content uploaded twice; both copies added to one collection, then one copy each to two collections | Same collection: first add 200, second add 400 with an error naming a duplicate, the second copy's file record remains. Two collections: both adds 200 |

What follows from these:

- **Probe 1** fixes the mechanism in §4.4: relink with `delete_file=false`.
- **Probe 2** is why an archived file keeps `status: current` (§4.1, §4.4).
- **Probe 3:** the `clive` model must use legacy function calling (§4.7).
  Group grants are enforced on the chat path. Two results are unexplained
  and are re-run in T5 on the real `clive` model: why default mode returns an
  empty answer, and why legacy mode without access returns an empty answer
  instead of a refusal. The probe was one run on a scratch model without
  `clive`'s saved parameters. The first attempt returned 400 on every chat
  until the test user was given read access to the base model (W3 §2.4).
- **Probe 4:** `apply` deletes the uploaded file when the add is refused, so
  no orphan is left, and reports the duplicate by `doc_id`. Duplicates are
  only detected inside one collection, so the old collection does not block
  the T8 re-ingest.
- **Upload timing:** `file/add` refuses a file that has not been processed,
  so uploads use `process_in_background=false`.
- **Reserved metadata names** (read in the installed v0.12.3 source, not
  probed): Open WebUI gives its own meaning to `knowledge_id`,
  `directory_id`, `channel_id` and `file_hash` in upload metadata. §4.1 uses
  none of them and must not in future.

### 4.6 The script

`scripts/kb/ingest.py`, built like the W4 runner (httpx, pydantic-settings,
PyYAML from the dev group; synchronous; counts-only console, root `CLAUDE.md`
§9):

| Command | Does | Network |
|---|---|---|
| `check` | Validates `kb/manifest.yaml` and `kb/layout.yaml`; source files exist; reports problems by `doc_id` and field | none |
| `setup` | Creates missing collections from the layout and sets their grants; groups must already exist | Open WebUI |
| `plan` | Compares the manifest with Open WebUI: new, new version, unchanged, skipped, errors, per collection | Open WebUI, read-only |
| `apply` | Carries out `plan`; idempotent (keyed on `doc_id`, `version`, `source_sha256`). With `--delete <doc_id>`, removes that document's files (§4.4) | Open WebUI |
| `verify` | Per collection: files, files missing a required field, `doc_id`s with more than one version outside the archive, files linked to both a collection and the archive | Open WebUI, read-only |

It uses only routes confirmed in the running v0.12.3: `POST /api/v1/files/`
(form field `metadata`), `POST /api/v1/knowledge/create`,
`/{id}/file/add`, `/{id}/file/remove` (with `delete_file=false` when
archiving, §4.4), `/{id}/access/update`,
`GET /api/v1/knowledge/{id}/files`, `GET /api/v1/groups/`. It never deletes a
collection and never creates or changes a model.

### 4.7 The `clive` model and the evaluation

A workspace model `clive` on the chosen base model, with every collection
except `kb-archive` attached and the base model's parameters saved on it
(thinking off, `num_ctx`; set by Alex on 2026-11-09). Read access: `staff`,
on `clive` and on its base model's model row (W3 §2.4). Function calling
is set to legacy: in default mode, knowledge attached to the model returned
no sources over the API (§4.5, probe 3).
Users chat with `clive`; each user retrieves only from collections their
groups can read (T2 item 3 confirms this). The runner then evaluates `clive`
as an admin, so the baseline covers every collection; access is tested
separately in T5. For that, `EVAL_KNOWLEDGE_ID` becomes optional: when it is
empty the runner sends no `files`, and retrieval uses the model's attached
collections (T8 step 3).

### 4.8 Retrieval settings (T7)

Candidate: a cross-encoder reranker run by Open WebUI itself
(sentence-transformers), e.g. `BAAI/bge-reranker-v2-m3`. It downloads the model
once from Hugging Face into Open WebUI's data volume (already backed up).
Then top-k about 20 and reranker top-k about 6. Final values come from the
T7 measurement. Alex approves the download.

Trade-offs: a reranker adds a few seconds per answer and some GPU memory next
to the chat model; without one, similar wording wins over the chunk that
answers (W4 T3 dry run).

## 5. Commands

```bash
uv run python scripts/kb/ingest.py check
uv run python scripts/kb/ingest.py setup
uv run python scripts/kb/ingest.py plan
uv run python scripts/kb/ingest.py apply
uv run python scripts/kb/ingest.py verify
uv run pytest -q -m "not integration"
uv run ruff check . && uv run ruff format --check .
python3 scripts/check-public-safe.py
```

## 6. Configuration

- `.env` (names only, placeholders in `.env.example`): `KB_OPENWEBUI_URL`,
  `KB_API_KEY` (admin key; may be the same key as `EVAL_API_KEY`),
  `KB_SOURCE_DIR` (folder holding the source files, outside the repo).
  T4 and T5 also use the W3 T2 test account, `OPENWEBUI_TEST_API_KEY`,
  `OPENWEBUI_TEST_USER_EMAIL` and `OPENWEBUI_TEST_USER_PASSWORD`; these are
  not in `.env.example` yet and get placeholders in T3.
- `kb/layout.yaml` (tracked): collections, descriptions, grants. No client
  data.
- `kb/manifest.yaml` (git-ignored, backed up by `scripts/backup.sh`, denied to
  Claude Code like the eval set): one entry per document, with the §4.1
  fields and the source path relative to `KB_SOURCE_DIR`.
- `kb/manifest.example.yaml` (tracked): invented entries only.
- Open WebUI settings changed in the Admin Panel: groups, the `clive` model,
  reranker and top-k (recorded by the runner's settings snapshot).

## 7. Folder structure

```text
kb/
  layout.yaml               tracked
  manifest.example.yaml     tracked
  manifest.yaml             git-ignored, backed up
scripts/kb/
  ingest.py
tests/
  test_kb_ingest.py
```

## 8. Files created / modified

- New: `scripts/kb/ingest.py`, `tests/test_kb_ingest.py`, `kb/layout.yaml`,
  `kb/manifest.example.yaml`, `kb/README.md` (conventions from §4).
- Modified: `.gitignore`, `.env.example`, `.claude/settings.json` (deny rules),
  `scripts/backup.sh` and `docs/recovery-plan.md` §7 (manifest backup),
  `scripts/eval/run_eval.py` and its tests (optional knowledge id, T8),
  `evaluation/README.md`, `tests/CLAUDE.md` (exception note), the three
  documents claiming reranking (T7), and §12's documents.

## 9. Verification

- Offline suite and whole-repo lint pass; `check-public-safe.py` 0 matches.
- T4: on synthetic documents, `plan` after `apply` reports 0 changes; a new
  version leaves exactly one `current` file per `doc_id` outside the archive.
- T5, as the test user:

| Collection | Expected |
|---|---|
| A `staff` collection, user in a child group | answers, sources cited |
| `kb-commercial`, user not in `sales`/`management` | no sources from it |
| `kb-archive` | never cited |

- T7 and T8: W4 runner counts (answered, facts, source groups) before and
  after, same question ids.

## 10. Rollback procedure

- Scripts and docs: revert the commit.
- Open WebUI: collections, groups and the `clive` model are removed in the
  Admin Panel; the old single collection is kept until Alex approves deleting
  it in T8, so evaluation and chat keep working throughout.
- Reranker: clear the engine and model in Admin Panel → Documents.
- Full restore: `docs/recovery-plan.md` from the backup taken at T8 step 2.

## 11. Common issues

- **"Duplicate content detected"** (400 or 500): the same text is already
  in Open WebUI; `plan` reports it per `doc_id`.
- **Regular user gets "Model not found":** the `clive` model or its base
  model has no read grant (W3 §2.4).
- **Answers empty or slow:** the base model's thinking is on (W4 T3 dry run).
- **An Open WebUI upgrade** can change these routes (W3 §2.8); re-run T4's
  synthetic test before ingesting after any upgrade (ADR-018).

## 12. Documentation updates

- `docs/STATUS.md`: W3 option B conditions as they are met; next task; the
  knowledge-base risk row.
- `docs/CHANGELOG.md`: one entry per merged task.
- `docs/README.md`: rows for this plan and `kb/README.md`; "Current state"
  cells of every living document changed.
- Reranking claims (T7, W3 §1.1): `docs/architecture.md`,
  `docs/PDDs/PDD-phase2.md` and the Phase 2 entry in `docs/CHANGELOG.md`. The
  last two record a completed phase, so they get a dated correction note, and
  only with Alex's approval.
- `evaluation/README.md` (T8).

## 13. Git commit

One commit per task, for example
`feat(kb): ingestion script with manifest and layout (option B T3)`.

## 14. Acceptance criteria

- [x] §4.1–§4.4 approved by Alex (condition 1)
- [x] T2 results recorded; version mechanism fixed
- [ ] `ingest.py` offline tests pass; whole-repo lint passes
- [ ] Live synthetic test passes and is cleaned up (condition 2)
- [ ] Groups, collections and the `clive` model exist; test-user access table passes (condition 3)
- [ ] Scanned PDFs and drawings spot-checked and a decision recorded (condition 4)
- [ ] Reranker and top-k measured; Alex's choice recorded
- [ ] Current files re-ingested with metadata; dry run reported
- [ ] `manifest.yaml` git-ignored, backed up and denied to Claude Code
- [ ] `STATUS.md`, CHANGELOG and `docs/README.md` updated
