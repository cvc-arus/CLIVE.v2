# CLIVE evaluation set

A repeatable way to measure CLIVE's answer quality, so that model, prompt and retrieval
changes are judged on evidence rather than impression. It comes from course correction W4
(`docs/sprints/course-correction/W4-evaluation.md`). Phase 3B's model choice will use
it.

> **Status of this folder:** W4 T1 design approved by Alex 2026-11-04; the runner,
> `scripts/eval/run_eval.py`, was added in W4 T3. Current status is in `docs/STATUS.md`.

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

`scripts/backup.sh` backs up `evaluation/eval-set.yaml` and `evaluation/results/` with the
private build notes (W4 T3; `docs/recovery-plan.md` §7). Claude Code's settings deny it
reading or editing them.

## Evaluation set format

`evaluation/eval-set.yaml` is a mapping with a `version` number and a `questions` list,
one entry per question, in the format Alex used for W4 T2 (2026-11-05). See
`eval-set.example.yaml`. The runner checks this structure before it sends anything and
reports problems by question id and field name only.

| Field | Type | Meaning |
|---|---|---|
| `id` | string, unique | Stable identifier, e.g. `L01` |
| `category` | `lookup` · `multi_doc` · `not_found` | `lookup`: the answer is in one document. `multi_doc`: it needs more than one. `not_found`: it is not in the knowledge base, so the correct answer says so. A `simpro` category is added in Phase 3B Sprint 1 |
| `question` | string | Asked exactly as a user would type it |
| `reference_answer` | string | The correct answer, for the person marking |
| `must_include` | list of lists of strings | Facts a correct answer must contain. Each inner list is one fact with its acceptable alternatives (e.g. `[1500 mm, 1.5 m]`). Empty for `not_found` |
| `source_groups` | list of lists of file names | Documents that hold the answer. Each inner list is one needed source with acceptable alternatives. Empty for `not_found` |
| `source_locator` | string | Where in the source the answer is (section, page or table), for the person marking |
| `distractors` | list of strings | Plausible wrong facts; one appearing in an answer is a warning sign |

Target mix for W4 T2: 20–30 questions, about 60 % `lookup`, 25 % `multi_doc` and
15 % `not_found`. Alex approves every question and expected answer. The set Alex wrote
has 40.

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
  (`utils/middleware.py`). With a collection attached there is **one item for the
  whole collection**: `source` holds only the collection's `id` and `type: collection`.
  The file of each retrieved chunk is in `metadata[i]` (`name`, `file_id`), aligned with
  `document[i]` and `distances[i]` (found in the T3 dry run, 2026-11-06).
- **No chat history is left behind:** a request without `chat_id` and `parent_id` is not
  saved as a chat (`main.py`, `utils/chat_id.py`).
- **Settings snapshot:** `GET {base_url}/api/v1/retrieval/config` (admin;
  `routers/retrieval.py`).

T3 re-checked them on 2026-11-06 against the running v0.12.3, and added the embedding
settings route (`GET /api/v1/retrieval/embedding`). If Open WebUI is upgraded, check the
source again before relying on them.

### Identity

The runner uses an **admin API key**, created by Alex and held in `.env` (Alex,
2026-11-04). This is because W3 T2 found that, as configured, no regular user can use
any model: a model without a `model` row is admin-only. An admin bypasses access checks
but gets the same retrieval and answers. **The evaluation therefore does not test access
control**; that was W3 T2's job, and Phase 3B's gateway owns it for Simpro.

### Configuration

The runner uses pydantic-settings and `.env`, like the rest of the repository (ADR-007).
The names and placeholders are in `.env.example`.

| Variable | Meaning |
|---|---|
| `EVAL_OPENWEBUI_URL` | Default `http://127.0.0.1:3000` |
| `EVAL_API_KEY` | Admin API key (secret; never printed or logged) |
| `EVAL_KNOWLEDGE_ID` | ID of the knowledge collection to attach |
| `EVAL_MODEL` | Model id to evaluate |
| `EVAL_TIMEOUT_SECONDS` | Per-question timeout; default 300 |

### Running it

```bash
uv run python scripts/eval/run_eval.py --ids L01,M01,N01   # dry run on chosen ids
uv run python scripts/eval/run_eval.py                     # the whole set
uv run python scripts/eval/run_eval.py --summarise evaluation/results/<file>.json
```

`--limit N` runs the first N questions (N is at least 1). `--summarise` rebuilds the Markdown summary of
a results file after marking. Exit codes: 0 all answered, 1 some questions failed, 2 a
setup problem (settings, eval set, Open WebUI unreachable or answering with something
other than its JSON settings, results folder not git-ignored, a results file whose
structure `--summarise` cannot read). Offline tests: `tests/test_eval_runner.py`.

### What a run records

`evaluation/results/<YYYY-MM-DD>_<model>.json` (git-ignored, mode 0600; a second run on
the same day gets `_2`, never overwriting) holds:

- **run:** date, runner commit, model id, knowledge collection id, the eval-set file's
  SHA-256, question counts, and a settings snapshot:
  - the Open WebUI version;
  - the embedding engine and model (`GET /api/v1/retrieval/embedding`);
  - an **allow-list** of retrieval settings from `GET /api/v1/retrieval/config`: top-k,
    reranker, relevance threshold, hybrid search and BM25 weight, full context, text
    splitter, chunk size and overlap, extraction engine. That endpoint also returns other
    services' API keys, so nothing outside the allow-list is kept;
  - a short SHA-256 of the RAG prompt template, so a template change is visible.
- **one record per question:**
  - `id`, `category`, `status` (`ok`, `error`, or `empty` when Open WebUI returned no
    answer text, which counts as an error), `http_status`, `error` (`HTTP nnn`, the
    exception type only, or `empty answer`);
  - the answer text;
  - the cited files: `name`, `file_id` and the distances of their retrieved chunks
    (not the chunk text);
  - latency in seconds and the `usage` token counts;
  - marking aids: `must_include` groups found in the answer, source groups among the
    cited sources, and distractors present. Facts match ignoring case, commas and
    spaces (`60 mm` matches `60mm`), but a fact that starts or ends with a digit is
    not found inside a longer number (`60mm` does not match `160mm`); file names match on letters and digits only
    (Open WebUI changes punctuation and spacing on upload), with or without the
    extension;
  - `mark`, empty until marked: one of `correct`, `partly`, `wrong`, `hallucinated`;
  - `marker_notes`.

The runner also writes a Markdown summary next to the JSON: run details, the settings,
and per-category counts (answered, errors, facts found, source groups cited, answers
with distractors, median latency). After marking, `--summarise` adds per-category
counts of each mark. The summary holds no question or answer text; W4 T4's committed
baseline is built from it.

**Marking** is manual to start with: Alex fills in `mark` for each record. The aids
help but do not decide. It is automated later only if that proves useful.

### Terminal output (root `CLAUDE.md` §9)

The runner prints only counts, timings, HTTP status codes and pass/fail, per question
`id` and per category. It never prints questions, answers, source names or document
text. Errors are reported by exception type only. Logging uses the same rule.

### Dependencies

- `httpx` and `pydantic-settings` are already pinned in the root `pyproject.toml`.
- Reading YAML uses `PyYAML==6.0.3`, in the **dev** dependency group (Alex,
  2026-11-04), because the runner is developer tooling and not part of `simpro_client`.

## Order of work

1. **T1** (this design): Alex approves it.
2. **T2 [HUMAN]:** Alex writes `evaluation/eval-set.yaml`. Claude Code may suggest
   candidate questions from documents Alex points to.
3. **T3:** the runner, with a dry run on 3 questions.
4. **T4:** the baseline. It waits for option B's conditions 1–3 (W3; `docs/STATUS.md`),
   because it should reflect the knowledge base going forward.
