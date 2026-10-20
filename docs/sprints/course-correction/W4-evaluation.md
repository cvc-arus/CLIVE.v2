# W4 — Evaluation Set and Baseline

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | W3 (baseline should reflect the setup going forward) |
| **Related** | Phase 3B PDD (model spike uses this set) |

## Goal

A repeatable way to measure answer quality, so model, prompt and retrieval
changes can be judged on evidence rather than impression. Phase 3B's model
choice will use it.

## Tasks

### T1 — Evaluation set format and runner design
Questions, expected answers, sources and recorded answers come from CVC's
documents, so they are client content and never tracked (ADR-017;
public-release sprint T7, Alex 2026-10-19). `evaluation/eval-set.yaml` and
`evaluation/results/` are git-ignored; T3 adds them to `scripts/backup.sh` so
they are backed up. Tracked: the runner, `evaluation/README.md`, an
`evaluation/eval-set.example.yaml` with invented questions showing the format,
and value-free summaries (per-category counts, model and settings).

1. Define `evaluation/eval-set.yaml` (`evaluation/` is created by this task; the file is git-ignored), one entry per question:
   `id`, `category` (lookup / multi-document / not-found / simpro),
   `question`, `expected_answer` (key facts), `expected_sources`, `notes`.
2. Design a runner that sends each question through Open WebUI as a user
   would (its chat completions API with an API key, using the relevant
   knowledge collection), and records the answer, cited sources, model, settings
   and timing. Confirm the exact API parameters from the running Open WebUI
   version's API documentation rather than assuming them.
**Stop point:** format and runner design for approval.

### T2 — [HUMAN] Write the questions
Alex writes 20–30 questions from real documents: about 60% simple lookups, 25%
needing more than one document, 15% whose answer is not in the knowledge base
(the correct answer is "not found"). Leave a `simpro` category empty; it is
filled in Phase 3B Sprint 1. Claude Code may suggest candidate questions from
documents Alex points to; Alex approves every question and expected answer.

### T3 — Runner implementation
`scripts/eval/run_eval.py` (created by this task; typed, logged, configurable via `.env`), writing
results to `evaluation/results/<date>_<model>.json` (git-ignored) plus a
Markdown summary. Scoring starts as manual marking (correct / partly / wrong /
hallucinated) recorded in the results; automate later only if useful. The
runner prints counts and pass/fail only, never questions or answers (root
`CLAUDE.md` §9). Add `evaluation/eval-set.yaml` and `evaluation/results/` to
`scripts/backup.sh`.
**Stop point:** dry run on 3 questions.

### T4 — Baseline
Run the full set with the current model and settings; Alex marks the answers;
commit a value-free summary as the baseline (`evaluation/baseline-<date>.md`:
model, settings and per-category counts of correct / partly / wrong /
hallucinated; no question or answer text). Run
`python3 scripts/check-public-safe.py` before committing.

## Verification
- Runner completes the full set without errors.
- Baseline summary shows per-category results and model/settings used.

## Rollback
`git revert <commit>`.

## Git commit
`feat(eval): evaluation set, runner and baseline results`

## Acceptance criteria
- [ ] 20–30 approved questions with expected answers and sources
- [ ] Runner in repo, documented in `evaluation/README.md` (created by this task)
- [ ] Value-free baseline summary committed with model and settings recorded; questions and results git-ignored and backed up
- [ ] `STATUS.md` updated
