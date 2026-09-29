---
description: Read-only check that documentation matches the code (no edits)
argument-hint: "[paths or git ref]  (default: changes on this branch vs origin/main, plus uncommitted)"
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git ls-files:*), Bash(git rev-parse:*), Bash(uv run pytest:*), Bash(uv run ruff check:*)
---

Run a documentation check. **This is read-only: do not create, edit, move or
delete any file.** Follow the rules in `docs/CLAUDE.md` and the document
types in `docs/README.md`.

## 1. Decide the scope

Arguments: `$ARGUMENTS`

- If the arguments are file or directory paths, check those documents.
- If the argument is a git ref (for example `HEAD~3` or a tag), check the
  documents affected by `git diff --name-only <ref>` plus uncommitted
  changes.
- If there are no arguments, use `git diff --name-only origin/main...HEAD`
  plus `git status --short`.
- If the argument is `all`, check every document listed in `docs/README.md`.

"Documents affected" means:
1. Changed Markdown files.
2. Living and reference documents that mention a changed code or config file,
   module, class, function, setting, env var, route or command. Find them
   with Grep.
3. `docs/CHANGELOG.md` whenever code changed.

Say which scope you used and list the documents in it before checking.

## 2. Check each document

Skip historical documents except for broken links and missing historical
headers; they are not meant to match current code.

For living and reference documents, check every factual claim:
- Files, modules, classes, functions, settings and env vars exist with the
  stated names.
- Routes, ports, container names and commands match `docker-compose.yml`,
  `pyproject.toml` and the code.
- Status claims (implemented / planned) match the code.
- Links and paths resolve.
- No volatile numbers (test counts, lint counts, hashes) in living documents.
- No fact duplicated from the document that owns it in `docs/README.md`.

Also check:
- Every file under `docs/` is listed in `docs/README.md`.
- Every ADR in `docs/ADR/` is in `ADR-index.md` with a status.
- If code changed, `CHANGELOG.md` has an entry for it.

Only run `uv run pytest` if a claim about tests is in scope. Afterwards, run
`git status --short`. If tracked `__pycache__` files show as modified, tell me
to restore them; do not restore them yourself.

## 3. Report

Start with the commit (`git rev-parse --short HEAD`) and scope. Then:

**Findings table**

| Document | Line or section | Claim | Actual (evidence) | Severity | Suggested fix |

Severity: **wrong** (contradicts code), **stale** (was true, no longer),
**unverifiable** (can't be checked from the repository), **structure**
(duplication, missing from index, bad filename, missing header).

**Summary**: number of findings per severity, and which documents are clean.

**Needs Alex's decision**: anything that can't be fixed without a decision.

Every finding needs evidence: a file path, a code excerpt, or command
output you ran. If you couldn't check something, list it as unverifiable.
Do not propose rewrites of whole documents; suggest the smallest fix.
