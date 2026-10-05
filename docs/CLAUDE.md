# CLAUDE.md — `docs/`

Complements the root `CLAUDE.md`. Applies to everything under `docs/`, and to
`README.md`, `structure.txt` and `services/simpro_mock/configuration.md`
when you edit them.

## 1. Source-of-truth rules

Documentation describes the repository. It is never evidence that something
exists.

1. Code and command output decide what is implemented.
2. ADRs (`docs/ADR/`) decide intended architecture and binding constraints.
3. PDDs (`docs/PDDs/`), scope (`docs/scope/`), `roadmap.md` and sprint
   reports (`docs/phase*/`) are context. Several are stale.

Before writing any statement about the code, open the file or run the command
that proves it. When a document disagrees with the code, record the
discrepancy (in your report, or in `known-issues.md` if asked). Do not
rewrite the code or the document to hide it.

Known stale or inaccurate documents are listed in `docs/README.md` §3
(living documents, "Current state" column) and §6 (historical documents
needing correction notes). Do not repeat their claims. That list is a
snapshot; re-verify before relying on this.

## 2. Implemented vs planned

Every status statement must be one of these, and must be checkable:

- **Implemented**: name the file(s). If you state test results, they must be
  from a command you ran in this session.
- **Implemented with deviations**: name the ADR or contract section it
  deviates from and describe the deviation.
- **Planned / Proposed**: say where it is planned (ADR, PDD, sprint), and say
  it does not exist yet.
- **Unknown**: say so rather than guessing.

Never describe planned features in the present tense. Never mark a sprint,
phase or ADR complete without evidence.

## 3. Verification evidence

- Only include command output you actually ran, copied as-is (trimmed with
  `...` if long), together with the commit it ran against
  (`git rev-parse --short HEAD`).
- Never write expected output as if it were real output. If you did not run
  it, say "not run" and why (e.g. Docker unavailable).
- Test counts, lint results and file lists must come from the current run,
  not from an earlier report.
- Link to code by repository path (e.g. `src/simpro_client/client.py`), not
  by line number, because line numbers go stale.

## 4. ADR rules

- Location: `docs/ADR/`. Naming: `adr-NNN-kebab-title.md`. The next free
  number is **011**. Add every ADR to `docs/ADR/ADR-index.md` in the same
  change.
- Minimum sections: Status, Context, Decision, Alternatives Considered,
  Consequences. Status is one of Proposed, Accepted / Approved, Superseded by
  ADR-NNN, Rejected, or Withdrawn (with a reason). Also record Deciders and a
  date.
- An ADR is required before: async I/O, new services or containers, new
  dependency categories, auth-flow changes, the Phase 3 → 4 handoff,
  persistence/caching, or changes to documented mock limitations.
- Do not edit the Decision of an Accepted/Approved ADR. Write a new ADR that
  supersedes it, and update the old one's Status line only.
- Claude drafts ADRs as **Proposed** with options and a non-binding
  recommendation. Only Alex accepts them. Do not fill in ADR-009's Decision.
- ADR-008 is **Withdrawn** (duplicate of ADR-010). Do not implement from it,
  cite it, or renumber it; ADR-010 is the authoritative record.
- `structure.txt` is generated. Regenerate it with the command in
  `docs/README.md` instead of editing it by hand.

## 5. Document types and where they go

| Content | Location |
|---|---|
| Architecture decisions | `docs/ADR/` |
| Phase design | `docs/PDDs/PDD-phaseN.md` |
| Sprint plans, contracts, reports | `docs/phaseN/` |
| Cross-cutting guides | `docs/architecture.md`, `installation.md`, `testing.md`, `development-standards.md` |
| Mock API reference | `docs/simpro-mock-api-reference.md` (generated from `services/simpro_mock/` code) |
| Discrepancies | `docs/known-issues.md` |
| Release history | `docs/CHANGELOG.md` (updated at the end of each sprint) |

- New files are Markdown with a `.md` extension and lowercase kebab-case
  names without spaces. Phase documents are prefixed with the phase, as in
  `docs/phase3/sprints/phase3-sprint4-contract.md`.

- Sprint reports are historical records. Do not rewrite them to match later
  code. If one contains a factual error, add a dated correction note at the
  end of the file, and only when asked.
- Each sprint's documentation update covers: what changed (with file paths),
  verification evidence, any known issues, and a CHANGELOG entry.

## 6. Style

- Markdown, Git-friendly: headings, short paragraphs, tables for comparisons,
  fenced code blocks with a language tag.
- Commands must be copy-pasteable and verified to exist (see root §6).
  Mention the `uv sync` vs `pip install -e ".[dev]"` pitfall where relevant.
- No secrets, tokens, real customer data or `.env` values in docs. Use
  `.env.example` names only.
- `ruff format --check .` also inspects Python code blocks inside Markdown
  (`docs/phase3/phase3-summary.md` and `phase3-sprint4-contract.md`
  currently fail it). Do not mass-reformat existing docs.
