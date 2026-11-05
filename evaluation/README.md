# CLIVE evaluation set

A repeatable way to measure CLIVE's answer quality, so that model, prompt and retrieval
changes are judged on evidence rather than impression. It comes from course correction W4
(`docs/sprints/course-correction/W4-evaluation.md`). Phase 3B's model choice will use
it.

> **Status of this folder:** W4 T1 design, approved by Alex 2026-11-04. The runner
> (`scripts/eval/run_eval.py`) does not exist yet; T3 builds it. Current status is in
> `docs/STATUS.md`.

## What is tracked and what is not

The questions, expected answers, sources and recorded answers come from CVC's documents.
They are client content, so they never reach git (ADR-017; public-release sprint T7).

| Path | Tracked? | Holds |
|---|---|---|
| `evaluation/README.md` | yes | This design |
| `evaluation/eval-set.example.yaml` | yes | The format, with invented questions only |
| `evaluation/eval-set.yaml` | **no** (`.gitignore`) | The real questions (Alex, W4 T2) |
| `evaluation/results/` | **no** (`.gitignore`) | Recorded answers and the per-run summaries |
| `evaluation/baseline-<date>.md` | yes (W4 T4) | Value-free summary: model, settings, per-category counts only |

T3 adds `evaluation/eval-set.yaml` and `evaluation/results/` to `scripts/backup.sh`.

## Evaluation set format

`evaluation/eval-set.yaml` is a YAML list with one entry per question. See
`eval-set.example.yaml`.

| Field | Type | Meaning |
|---|---|---|
| `id` | string, unique | Stable identifier, e.g. `L01` |
| `category` | `lookup` · `multi-document` · `not-found` · `simpro` | `lookup`: the answer is in one document. `multi-document`: it needs more than one. `not-found`: it is not in the knowledge base, so the correct answer says so. `simpro`: left empty until Phase 3B Sprint 1 |
| `question` | string | Asked exactly as a user would type it |
| `expected_answer` | list of strings | The key facts a correct answer must contain (for `not-found`: that the information is not available) |
| `expected_sources` | list of strings | File names in the knowledge collection that hold the answer (empty for `not-found`) |
| `notes` | string, optional | Marking guidance, e.g. acceptable variations |

Target mix for W4 T2: 20–30 questions, about 60 % `lookup`, 25 % `multi-document` and
15 % `not-found`. Alex approves every question and expected answer.

## Runner design

The runner sends each question through Open WebUI as a user would: through its chat
completions API, with the knowledge collection attached. Each run is recorded with
enough detail to compare it with the next.

### API, confirmed against the running Open WebUI v0.12.3

These facts were confirmed on 2026-11-04 from the source inside the running
`ghcr.io/open-webui/open-webui:v0.12.3` container, under `backend/open_webui/`:

- **Endpoint:** `POST {base_url}/api/chat/completions` (`main.py`), with the header
  `Authorization: Bearer <API key>`. API keys must be enabled (`ENABLE_API_KEYS`); W3 T2
  already used one.
- **Request body:**

  ```json
  {
    "model": "<model id>",
    "messages": [{"role": "user", "content": "<question>"}],
    "files": [{"type": "collection", "id": "<knowledge collection id>"}],
    "stream": false
  }
  ```

  - `files` is copied into the request metadata (`main.py`).
  - The RAG step (`chat_completion_files_handler` in `utils/middleware.py`) retrieves
    from each item.
  - `type: "collection"` resolves a knowledge collection, with an access check
    (`retrieval/utils.py`).
- **Retrieval steps:**
  1. Open WebUI first asks the task model to write search queries from the question.
  2. It then searches with `rag.top_k`, the reranker (if configured), `rag.top_k_reranker`,
     `rag.relevance_threshold` and `rag.enable_hybrid_search` with its BM25 weight.
  3. `rag.full_context` is applied when enabled.

  These settings affect the answer, so every run records them.
- **Response:** the OpenAI-style body (`choices[0].message.content`, `usage`), with a
  top-level `sources` list added by `merge_events_into_response`
  (`utils/middleware.py`). Each source has `source.id` and `source.name`, plus
  `document[]`, `metadata[]` and `distances[]`.
- **No chat history is left behind:** a request without `chat_id` and `parent_id` is not
  saved as a chat (`main.py`, `utils/chat_id.py`).
- **Settings snapshot:** `GET {base_url}/api/v1/retrieval/config` (admin;
  `routers/retrieval.py`).

T3 re-checks these against the running version before it relies on them. If Open WebUI
has been upgraded since 2026-11-04, the source must be checked again.

### Identity

The runner uses an **admin API key**, created by Alex and held in `.env` (Alex,
2026-11-04). This is because W3 T2 found that, as configured, no regular user can use
any model: a model without a `model` row is admin-only. An admin bypasses access checks
but gets the same retrieval and answers. **The evaluation therefore does not test access
control**; that was W3 T2's job, and Phase 3B's gateway owns it for Simpro.

### Configuration (proposed names; fixed in T3)

The runner uses pydantic-settings and `.env`, like the rest of the repository (ADR-007).
Nothing is added to `.env.example` until T3.

| Variable | Meaning |
|---|---|
| `OPENWEBUI_BASE_URL` | Default `http://127.0.0.1:3000` |
| `OPENWEBUI_EVAL_API_KEY` | Admin API key (secret; never printed or logged) |
| `EVAL_KNOWLEDGE_ID` | ID of the knowledge collection to attach |
| `EVAL_MODEL` | Model id to evaluate, e.g. the current default |
| `EVAL_TIMEOUT_SECONDS` | Per-question timeout |

### What a run records

`evaluation/results/<YYYY-MM-DD>_<model>.json` (git-ignored) holds:

- **run:** date, runner commit (`git rev-parse --short HEAD`), Open WebUI version, model
  id, the eval-set file's SHA-256, and the retrieval settings snapshot.
- **one record per question:**
  - `id`, `category`;
  - the answer text;
  - the cited sources (`source.name`, `source.id`) and their distances;
  - latency in seconds, the `usage` token counts, and the HTTP status;
  - `error`: exception type only;
  - `mark`, empty until marked: one of `correct`, `partly`, `wrong`, `hallucinated`;
  - `marker_notes`.

The runner also writes a Markdown summary next to the JSON in `evaluation/results/`.
Before marking, it shows source hit rates (an expected source was cited, or was not)
per category. After marking, it shows per-category counts of each mark.

**Marking** is manual to start with (W4 T3): Alex fills in `mark` for each record. It
is automated later only if that proves useful.

### Terminal output (root `CLAUDE.md` §9)

The runner prints only counts, timings, HTTP status codes and pass/fail, per question
`id` and per category. It never prints questions, answers, source names or document
text. Errors are reported by exception type only. Logging uses the same rule.

### Dependencies

- `httpx` and `pydantic-settings` are already pinned in the root `pyproject.toml`.
- Reading YAML needs `PyYAML`, which is not a dependency today. **Decided (Alex,
  2026-11-04):** T3 adds it, exact-pinned, to the **dev** dependency group, because the
  runner is developer tooling and not part of `simpro_client`.

## Order of work

1. **T1** (this design): Alex approves it.
2. **T2 [HUMAN]:** Alex writes `evaluation/eval-set.yaml`. Claude Code may suggest
   candidate questions from documents Alex points to.
3. **T3:** the runner, with a dry run on 3 questions.
4. **T4:** the baseline. It waits for W3, because it should reflect the knowledge base
   going forward.
