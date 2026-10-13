# W6 — Documentation Consolidation and Phase 3 Sign-off

| | |
|---|---|
| **Template** | Short |
| **Status** | Approved |
| **Depends on** | Nothing (T1 runs first in the sprint) |
| **Related** | `docs/documentation-change-list.md`, `docs/simpro/simpro-api-findings.md` |

## Goal

Make `docs/STATUS.md` the single source of current status, record the Phase 3
test evidence, record superseded scope documents as historical, and remove the
inconsistencies found in the October review. Drift between documents has
already caused six conflicts; one living status file stops that recurring.

Already done at intake (2026-10-13): Phase 3 was closed on 2026-10-09 and that
is recorded in `docs/roadmap.md` and `docs/CHANGELOG.md` (PR #45); the package
files, including `docs/STATUS.md`, the templates and the two skills, are in the
repo. Merge inputs for T3 and T6 are in
`docs/sprints/course-correction/merge-inputs/`.

## Tasks

### T1 — Record Phase 3 test evidence and make STATUS.md the status owner
1. Run the full test suite with the mock up (`uv run pytest -q`; root
   `CLAUDE.md` §6 and `tests/CLAUDE.md`) and capture: pass/fail/skip counts,
   coverage if configured, and the commit hash (`git rev-parse --short HEAD`).
2. Record that evidence in a **historical** record, not in `STATUS.md`
   (`docs/README.md` §2 bans test counts and commit hashes in living documents):
   `docs/phase3/phase3-signoff.md`, headed
   `> Historical record as of <date>, commit <hash>. Not maintained.`, and add
   its row to `docs/README.md` §6. Link it from `STATUS.md`'s Phase 3 row.
3. Transfer ownership of phase status from `docs/roadmap.md` to `docs/STATUS.md`:
   - `docs/README.md` §2/§3: `STATUS.md` owns phase, sprint and workstream
     status; add its §3 row; change `roadmap.md`'s "Owns" cell to the phase list
     and scope only.
   - `docs/CLAUDE.md`: status statements live only in `STATUS.md`.
   - `docs/roadmap.md`: replace the Status column with a link to `STATUS.md`.
4. Add a `docs/CHANGELOG.md` entry: course correction sprint started; STATUS.md
   now owns status. (The Phase 3 close entry already exists, dated 2026-10-12.)
**Stop point:** show test summary and diffs.

### T2 — Record superseded scope documents as historical
The scope documents are already historical records in `docs/scope/`, each with
a header (`docs/README.md` §6): `clive-scope.md` (was `Clive_Scope.txt`),
`scope-rev2.md` (was `RevisedScope.txt`) and `master-project-document.md`.
Scope Revision 3 was added at intake as `docs/scope/scope-rev3.md`, already
bannered. Do not move or rewrite any of them.
1. Add `scope/scope-rev3.md` to `docs/README.md` §6 as historical.
2. Search living documents for links to `Clive_Scope.txt`, `RevisedScope.txt`
   or `scope-revision-3.md` and point them at the `docs/scope/` files.
**Stop point:** list updated links.

### T3 — ADR index, new ADRs and reference checks
1. **Index:** merge
   `docs/sprints/course-correction/merge-inputs/ADR-index-additions.md` into
   `docs/ADR/ADR-index.md`: add the naming convention, numbering rules and
   statuses; add rows for ADR-014 and ADR-015 in the index's existing columns
   (`#`, Title, Phase, Status); set "Next free number" to ADR-016. Check every
   existing row against its ADR file (number, title, status, date); do not
   guess. Report any file that breaks the convention, but do not rename
   existing files without Alex's approval. Do not add a separate `README.md` in
   `docs/ADR/`. Update `docs/CLAUDE.md` §4's next free number (014 → 016) and
   add both ADRs to `docs/README.md` §5 in the same commit.
2. **New ADRs** (ADR-001 to ADR-013 already exist; do not touch their numbers).
   Added at intake with status **Proposed**:
   - `adr-014-simpro-access-control-model.md`: CLIVE-managed roles, deny by default
   - `adr-015-conversational-access-approach.md`: tool calling over a fixed query catalogue

   The gateway decision is **ADR-009** (decided 2026-10-09, PR #44); there is
   no separate access-mechanism ADR. Intake (2026-10-13) found no earlier draft
   copies of these ADRs under other numbers. If any appear, **stop and list
   them**; delete them only after Alex confirms. Never overwrite the existing
   ADR-009, ADR-011 or ADR-012. Do not change any status to Accepted; that is
   Alex's decision.
3. **Consistency with earlier ADRs:** no amendment sections. `docs/CLAUDE.md`
   §4 allows only a superseding ADR plus a Status-line update on the old one.
   ADR-006's Status line already records that ADR-009 partially supersedes it
   (PR #45). List for Alex, without editing: ADR-009's Status line still reads
   Proposed, and its `Related:` line cites "ADR-011 (Simpro data access control
   model, proposed)", which is now ADR-014.
4. Confirm that no living document cites ADR-005 for the rate limiter
   (`roadmap.md` was fixed on 2026-10-02). The remaining mentions are in
   historical documents (`docs/scope/scope-rev2.md`,
   `docs/phase3/sprints/phase3-sprint4-contract.md`); add a dated correction
   note there only if Alex asks.
5. `docs/PDDs/PDD-phase3.md` has no ADR table (it is an as-built rewrite,
   §1–§8). Record ADR-009's decision where §4, §5, §7 and §8 still say the
   handoff ADR is not written (revision already "To do" in `docs/README.md` §5).
**Stop point:** show the index and each changed reference.

### T4 — Apply Simpro findings to Phase 3B documents
Using `docs/simpro/simpro-api-findings.md` section 2:
1. Phase 3B PDD: add sandbox contract tests to the testing strategy; make
   Company IDs configuration (remove assumptions of 1 and 2 outside the mock);
   add custom fields to field classification; add "course correction sprint
   complete" to entry criteria; model spike uses the W4 evaluation set.
2. ADR-014: add a Context/Decision note that CLIVE roles operate inside a
   dedicated read-only Simpro security group, and a "Revisit if" item for
   Option 2 once sandbox testing can verify per-user behaviour.
**Stop point:** show diffs.

### T5 — Phase 3B and the gateway in living documents
`docs/scope/master-project-document.md` is a historical record
(`docs/README.md` §6) and is not edited.
1. Add Simpro conversational access and Phase 3B to `docs/roadmap.md`
   (order: "see `docs/STATUS.md`").
2. Replace any statement in a living document or PDD that Phase 4 imports
   `simpro_client` directly with a reference to ADR-009 (gateway). Known
   remaining case: `docs/PDDs/PDD-phase4.md` §1, §2, §4 and its diagram.
**Stop point:** show diffs.

### T6 — Templates and Claude Code configuration
1. Templates `docs/templates/sprint-full.md` and `sprint-short.md` and skills
   `.claude/skills/sprint-task/` and `.claude/skills/status-update/` were added
   at intake. Alex restarts Claude Code and confirms `/sprint-task` and
   `/status-update` appear.
2. Merge `docs/sprints/course-correction/merge-inputs/CLAUDE-root-additions.md`
   into the root `CLAUDE.md` (merge, don't replace existing content; flag any
   conflicts instead of resolving silently).
3. Root `CLAUDE.md` §5 and `docs/development-standards.md` §8 require the full
   14-section format for all sprint work. Amend both so the short template is
   allowed for sprints that do not change infrastructure, security or data.
4. Update `docs/CLAUDE.md`: historical documents are read-only
   (`docs/README.md` §6); new sprints use the templates; extend the §5
   placement table with `docs/sprints/`, `docs/templates/`, `docs/simpro/` and
   `docs/reviews/`.
5. Add every new document from this sprint's package to `docs/README.md`
   (living, reference, decision or historical) in the same commit.
**Stop point:** show diffs; Alex restarts Claude Code and confirms `/sprint-task` appears.

### T7 — Remaining high-priority change-list items
1. Work through the "High" items in `docs/documentation-change-list.md` not
   already covered by T1–T6 (architecture, roadmap, security, Phase 4 PDD entry
   criteria).
2. Tick each item in the change list as done, with the commit hash.
**Stop point:** list items done and any left with reasons.

## Verification
- `grep -rn "ADR-005" docs/ | grep -iE "rate|req/sec"` returns only historical documents.
- `grep -rln "Current Status" docs/ --exclude-dir=scope --exclude-dir=phase3 --exclude-dir=sprints --exclude=documentation-change-list.md`
  returns nothing (status sections remain only in historical documents).
- `grep -rn "Clive_Scope.txt\|RevisedScope.txt\|scope-revision-3" docs/` returns
  only historical documents and this sprint's own files.
- `uv run pytest -q` still passes (documentation-only changes).

## Rollback
`git revert <commit>` per task.

## Git commit
One commit per task, e.g.
`docs(status): record Phase 3 test evidence; STATUS.md owns status`
`docs: record scope revision 3 as historical`
`docs(adr): merge ADR index conventions; add ADR-014 and ADR-015 rows`

## Acceptance criteria
- [ ] Phase 3 test evidence (commit hash, test summary) recorded in a historical record and linked from `STATUS.md`
- [ ] `STATUS.md` is the only living document stating current status; `docs/README.md`, `docs/CLAUDE.md` and `roadmap.md` updated to match
- [ ] Scope documents, including `scope-rev3.md`, listed as historical in `docs/README.md` §6
- [ ] `ADR-index.md` complete with naming convention; ADR-014 and ADR-015 present as Proposed; ADR-009's Status and `Related:` lines raised with Alex
- [ ] Simpro findings applied to the Phase 3B PDD and ADR-014
- [ ] Templates, skills and `CLAUDE.md` updates in place and working
- [ ] High-priority change-list items done or explicitly deferred
