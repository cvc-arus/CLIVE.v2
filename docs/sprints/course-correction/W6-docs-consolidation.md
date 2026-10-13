# W6 — Documentation Consolidation and Phase 3 Sign-off

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | Nothing (T1 runs first in the sprint) |
| **Related** | `docs/documentation-change-list.md`, `docs/simpro/simpro-api-findings.md` |

## Goal

Make `docs/STATUS.md` the single source of current status, record Phase 3
sign-off, archive superseded scope documents, and remove the inconsistencies
found in the October review. Drift between documents has already caused six
conflicts; one living status file stops that recurring.

## Tasks

### T1 — Record Phase 3 sign-off and install STATUS.md
1. Run the full test suite (all packages) and capture: pass/fail counts, coverage
   if configured, and the current commit hash.
2. Add `docs/STATUS.md` (from this sprint's delivery) if not present.
3. In `STATUS.md`, record Phase 3 as complete with the date, commit hash and test summary.
4. Add a `CHANGELOG.md` entry: Phase 3 complete; course correction sprint started.
**Stop point:** show test summary and diffs.

### T2 — Archive superseded documents
1. Create `docs/history/` if absent.
2. `git mv` the original scope (`Clive_Scope`), Scope Revision 2 (`RevisedScope`)
   and Scope Revision 3 into `docs/history/`. Keep contents unchanged except a
   one-line banner at the top: `> Historical — superseded by docs/STATUS.md and docs/course-correction-plan.md (2026-10-12).`
3. Search the repo for links to the moved files and update them.
**Stop point:** list moved files and updated links.

### T3 — ADR index, new ADRs and reference fixes
1. **Index:** the repo already has `docs/ADR/ADR-index.md`. Merge
   `ADR-index-additions.md` (delivered at the package root) into it: add the
   naming convention and numbering rules, add rows for ADR-014 to ADR-016, and
   set "Next free number" to ADR-017. Check every existing row against its ADR
   file (number, title, status, date); do not guess. Report any file that breaks
   the convention, but do not rename existing files without Alex's approval.
   Do not add a separate `README.md` in `docs/ADR/`.
2. **New ADRs** (ADR-001 to ADR-013 already exist; do not touch their numbers).
   Add with status **Proposed**:
   - `adr-014-simpro-access-mechanism.md`: gateway as the single Simpro access point
   - `adr-015-simpro-access-control-model.md`: CLIVE-managed roles, deny by default
   - `adr-016-conversational-access-approach.md`: tool calling over a fixed query catalogue
   If any earlier draft copies exist in the repo (`ADR-009-simpro-access-mechanism.md`,
   `ADR-011-simpro-access-control-model.md`, `ADR-012-conversational-access-approach.md`,
   or `adr-014`/`adr-015` files with different titles), **stop and list them**;
   delete them only after Alex confirms. Never overwrite the existing ADR-009,
   ADR-011 or ADR-012. Do not change any status to Accepted; that is Alex's decision.
3. **Consistency with earlier ADRs:** read ADR-006 (library-first
   architecture) and ADR-009 (Phase 3 → Phase 4 handoff, decided in PR #44).
   - If ADR-014 refines them (for example, ADR-009 already chose a service, or
     allows direct import that ADR-014 now restricts): add a dated
     `## Amendment` section to each, pointing to ADR-014, and mark ADR-014's
     relationship accordingly.
   - If ADR-014 contradicts an accepted decision in a way an amendment can't
     reconcile: **stop and report** before changing anything.
4. Replace references to the rate limiter as "ADR-005" with ADR-010.
5. Align the ADR table in `PDD-phase3.md` with the actual ADRs (note the
   original proposed numbering as historical).
**Stop point:** show the index and each changed reference.

### T4 — Apply Simpro findings to Phase 3B documents
Using `docs/simpro/simpro-api-findings.md` section 2:
1. Phase 3B PDD: add sandbox contract tests to the testing strategy; make
   Company IDs configuration (remove assumptions of 1 and 2 outside the mock);
   add custom fields to field classification; add "course correction sprint
   complete" to entry criteria; model spike uses the W4 evaluation set.
2. ADR-015: add a Context/Decision note that CLIVE roles operate inside a
   dedicated read-only Simpro security group, and a "Revisit if" item for
   Option 2 once sandbox testing can verify per-user behaviour.
**Stop point:** show diffs.

### T5 — Master document trimmed to stable content
1. In the master project document, remove or replace status sections
   ("Current Status", phase status) with a link to `docs/STATUS.md`.
2. Keep vision, principles, standards and module descriptions.
3. Add Simpro conversational access under the Simpro Integration module and
   Phase 3B to the roadmap section (as "see STATUS.md for order").
4. Replace any statement that Phase 4 imports `simpro_client` directly with a
   reference to ADR-014 (gateway), wherever it appears in living documents.
**Stop point:** show diffs.

### T6 — Templates and Claude Code configuration
1. Add `docs/templates/sprint-full.md` and `sprint-short.md`.
2. Add `.claude/skills/sprint-task/SKILL.md` and `.claude/skills/status-update/SKILL.md`.
3. Merge `CLAUDE-root-additions.md` into the root `CLAUDE.md` (merge, don't
   replace existing content; flag any conflicts instead of resolving silently).
4. Update `docs/CLAUDE.md` to state: status lives only in `STATUS.md`;
   `docs/history/` is read-only; new sprints use the templates.
**Stop point:** show diffs; Alex restarts Claude Code and confirms `/sprint-task` appears.

### T7 — Remaining high-priority change-list items
1. Work through the "High" items in `docs/documentation-change-list.md` not
   already covered by T1–T6 (architecture, roadmap, security, Phase 4 PDD entry
   criteria).
2. Tick each item in the change list as done, with the commit hash.
**Stop point:** list items done and any left with reasons.

## Verification
- `grep -rn "ADR-005" docs/` returns no living-document references to the rate limiter.
- `grep -rln "Current Status" docs/ --exclude-dir=history` returns no status
  sections outside `STATUS.md`.
- All links to moved files resolve (`grep` for old paths returns nothing outside `docs/history/`).
- Test suite still passes (documentation-only changes).

## Rollback
`git revert <commit>` per task. `git mv` is reversible the same way.

## Git commit
One commit per task, e.g.
`docs(status): record Phase 3 sign-off and add STATUS.md`
`docs: archive superseded scope documents to docs/history`
`docs(adr): add ADR index; fix rate limiter references`

## Acceptance criteria
- [ ] Phase 3 sign-off recorded with commit hash and test summary
- [ ] `STATUS.md` is the only living document stating current status
- [ ] Superseded scope documents are in `docs/history/` with banners
- [ ] `ADR-index.md` complete with naming convention; ADR-014, ADR-015 and ADR-016 present as Proposed; ADR-006 and ADR-009 amended if needed
- [ ] Simpro findings applied to the Phase 3B PDD and ADR-015
- [ ] Templates, skills and `CLAUDE.md` updates in place and working
- [ ] High-priority change-list items done or explicitly deferred
