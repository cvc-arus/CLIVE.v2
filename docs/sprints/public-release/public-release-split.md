# Public release — split private build facts out, then publish a clean repository

| | |
|---|---|
| **Template** | Full (changes secrets handling, backups, git history and the GitHub remote) |
| **Status** | Approved 2026-10-19 (Alex); decisions D1–D7 recorded in §4.4. Course correction paused meanwhile |
| **Branch** | `chore/public-release-split` |
| **Depends on** | Privacy audit of 2026-10-19 (report kept outside the repo); a quiet point with no open feature branches (T10 rewrites every commit) |
| **Related** | ADR-017 (drafted in T1); root `CLAUDE.md` §3 and §9; `scripts/backup.sh`; `docs/recovery-plan.md` |

This plan deliberately names sensitive items by **category only**. Their values
go in the untracked private store created in T2, never in this file.

## 1. Goal

Make the CLIVE repository publishable. Every fact specific to CVC's Simpro
build or host moves to an untracked, backed-up private store or to `.env`. The
tracked tree refers to those facts only by placeholder or variable name. The
published repository's **entire history**, not just HEAD, is proven free of
them.

## 2. Business value

- **A public repository** can be shared with collaborators, vendors and future
  hires without a separate sanitised copy.
- **One rule for where build facts live** stops the slow spread of those
  details across docs. The audit found them in about 16 tracked files.
- **An automated check** stops new ones being committed.
- **The private facts become recoverable from backup.** Today they exist only
  in git.

## 3. Tasks

One task per session (`/sprint-task docs/sprints/public-release/public-release-split.md <id>`).

### T0 — [HUMAN] Decisions — done 2026-10-19

Alex answered D1–D7; the answers are recorded in §4.4.

**Naming (D4):** the project owner is referred to as **Alex** everywhere,
replacing "Alex". Living documents change in T5, historical ones in T6 or T10,
and commit messages in T10.

### T1 — Draft ADR-017: public repository and private build facts

Draft `docs/ADR/adr-017-public-repository-private-build-facts.md` as
**Proposed**, with options and a recommendation, and add its index row. It
records:

- the rule (no build- or host-specific facts in tracked files);
- the private store's location;
- the guard script;
- the publication method (D1).

Alex accepts it before T10. **Stop point:** ADR drafted; Alex reviews.

### T2 — Private store, templates and `.gitignore`

1. Add to `.gitignore`:
   - `docs/simpro/private/`
   - `.env.*` and `!.env.example`
   - the data-artefact patterns from the audit (`*.csv`, `*.xlsx`, `*.db`,
     `*.sqlite*`, `*.parquet`, `*.pkl`, `*.dump`, `exports/`, `dumps/`,
     `uploads/`, `chroma/`, `vectorstore/`)
   - `deploy/smartd/smartd.conf.local` and `deploy/systemd/*.local`
2. Create the untracked `docs/simpro/private/` with mode 0700:
   - `cvc-simpro-build.md`: the build facts moved out of tracked docs (company
     IDs in use, other companies in the build, the API application's permission
     level, the environment type, smoke-check specifics, access dates).
   - `public-deny-list.txt`: one regex per line with an ID, matching every
     sensitive value. It is the input to T3.
   - `filter-repo-replacements.txt` and `filter-repo-mailmap.txt`: inputs to
     T10. The old mock DB password is extracted into this file by a script and
     is never printed.
3. Create the tracked template `docs/simpro/private-notes.template.md`. It has
   the headings of `cvc-simpro-build.md` and placeholder text only, so a fresh
   clone knows what to fill in.
4. Extend `scripts/backup.sh` to back up `docs/simpro/private/`:
   - encrypted with `BACKUP_GPG_RECIPIENT` when it is set;
   - otherwise copied into the 0700 backup folder with a `NOTES.txt` warning
     (D6).
   - Add the item to the inventory in `docs/recovery-plan.md` §7.
5. Licence (D7):
   - add a root `LICENSE`: a proprietary "all rights reserved" notice, copyright CVC;
   - set `license = { text = "Proprietary" }` and the classifier
     `License :: Other/Proprietary License` in both `pyproject.toml` files;
   - re-run `uv lock --check` to confirm the lock files are unaffected.

**Stop point:**
- `git check-ignore docs/simpro/private/cvc-simpro-build.md` succeeds.
- `git status` shows no private file.
- One manual backup run lists the new item in `MANIFEST.txt`.

### T3 — Guard script `scripts/check-public-safe.py`

Standard library only. It reads `docs/simpro/private/public-deny-list.txt` and
scans:
- by default, every tracked file;
- with `--history`, every blob reachable from any ref, plus commit messages.

It prints only `path:line:pattern-id`, never the matched text, and exits 1 on
any hit. If the deny-list is missing it exits 2, so the check can't pass
silently on a fresh clone.

**Stop point:** a baseline run against current HEAD lists the expected hits.
That list is the work queue for T4–T6.

### T4 — Configuration and code: values become settings

1. `.env.example` (the template Alex completes):
   - live company IDs become commented placeholders
     (`# SIMPRO_COMPANY_ID_SERVICE=<service-company-id>`);
   - the mock values (`1`, `2`) stay active;
   - `BACKUP_DIR` becomes `<backup-dir-on-other-disk>`;
   - add `SIMPRO_LIVE_COMPANY_IDS=<id>,<id>` (see step 2).
2. `tests/test_live_contract.py`:
   - replace the hardcoded `LIVE_COMPANY_IDS` set with a small
     test-local `BaseSettings` that reads `SIMPRO_LIVE_COMPANY_IDS` from the
     environment or `.env`. It stays in the test, because `simpro_client` must
     hold no CLIVE specifics (ADR-006).
   - The module skips unless exactly two IDs are set and they equal
     `SIMPRO_COMPANY_ID_SERVICE`/`_PROJECTS`.
   - The request hook keeps blocking every company-scoped route outside that
     set.
   - Reword docstrings and messages to name the variables, not the values.
3. `tests/test_pagination.py`: replace the live-looking company IDs in the
   mocked `/companies/` fixture with synthetic ones.
4. `deploy/smartd/smartd.conf`:
   - disk IDs and the home path become placeholders (`<data-disk-by-id>`,
     `<os-disk-by-id>`);
   - the installed copy keeps real values in the untracked
     `smartd.conf.local`.
5. `deploy/systemd/clive-backup.service`:
   - the repository path and user become placeholders (`<repo-dir>`,
     `<user>`);
   - `docs/installation.md` §9 gives the one `sed` command that renders the
     installed copy.
   - The unit in `/etc/systemd/system/` is unchanged; no reinstall is needed.

**Stop point:**
- `uv run pytest -q -m "not integration"` passes.
- `uv run pytest -m live --co -q` collects the live tests, and they skip
  without the opt-in.
- ruff passes.
- `check-public-safe.py` shows no hits in these files.

### T5 — Living documentation: placeholders and links

Replace "Alex" with "Alex" (D4, whole word, case-sensitive) in every living
document, including all `CLAUDE.md` files and `.claude/` commands and skills.
Then rewrite each hit from T3 so that it names the variable
(`SIMPRO_COMPANY_ID_SERVICE`) or links to the private store ("see the private
build notes"). Keep the **rules** intact. For example, "only the two configured
company IDs are ever queried" and "never write, whatever the credentials
permit" stay binding; only their values move out.

Files from the audit:
- `CLAUDE.md`
- `services/simpro_mock/CLAUDE.md`
- `tests/CLAUDE.md`
- `docs/STATUS.md`
- `docs/README.md`
- `docs/ADR/ADR-index.md`
- `docs/ADR/adr-014-simpro-access-control-model.md` (Proposed, so it may be
  edited; Alex confirms)
- `docs/course-correction-plan.md`
- `docs/sprints/course-correction/W1-simpro-access.md` and `W6-docs-consolidation.md`
- `docs/testing.md`
- `docs/simpro/simpro-api-findings.md` (split: Simpro's public API behaviour
  stays, CVC's build facts move)
- `docs/simpro/mock-vs-public-api.md`
- `docs/recovery-plan.md` (developer email in the GPG example, drill
  container IP, home paths)
- `docs/installation.md`
- `docs/architecture.md`

Re-verify the list with T3's output before editing.

**Stop point:**
- `check-public-safe.py` reports hits only in the T6 and T7 files.
- `/doc-check` shows no broken links.

### T6 — Historical documents [needs Alex's approval per `docs/CLAUDE.md` §5]

Historical files with hits (from T3), for example:
- `docs/CHANGELOG.md`
- `docs/phase3/sprints/phase3-sprint4-preflight-audit.md` (home paths)
- `docs/sprints/course-correction/merge-inputs/CLAUDE-root-additions.md`

For each one, Alex picks **edit in place**, adding a dated note
`> 2026-10-xx: values replaced with placeholders for public release`, or
**replace in history only**, letting T10's replacement rules handle it. Either
way the published copy holds no values.

**Stop point:** zero tracked hits outside T7 files.

**Applied 2026-10-19:** the rename to Alex (D4) was applied in place to every
file, historical ones included. For build and host values, two historical
files still had hits: `docs/phase3/sprints/phase3-sprint4-preflight-audit.md`
(home paths) and
`docs/sprints/course-correction/merge-inputs/CLAUDE-root-additions.md` (one
environment phrase). They are left as they are and handled by T10's
replacement rules ("replace in history only"), so the published copy has no
values. Alex may still choose to edit them in place instead.

### T7 — Business-context review (Claude proposes, Alex decides)

Claude reads the documents that describe CVC's business rather than the code,
and proposes a status for each: **public**, **private** or **public after
edits** (naming the passages to change, by category only). Alex decides.
The documents:
- `docs/scope/` (including `master-project-document.md` and `clive-scope.md`)
- `docs/PDDs/`
- `docs/roadmap.md`
- `docs/course-correction-plan.md`
- `docs/sprints/course-correction/W2-docgen-value-check.md`, `W3-kb-audit.md`
  and `W4-evaluation.md`

Private files move to the private store and are listed for removal from all
history in T10.

**Stop point:** a list in this file, with no values in it.

**Decision (Alex, 2026-10-19): proposal accepted as written.** The scope documents, PDDs, roadmap, course-correction plan, recovery plan and STATUS stay public unchanged. W2–W4 were edited to redirect their outputs (W2 figures and W3 names to `docs/simpro/private/`; W4's `evaluation/eval-set.yaml` and `evaluation/results/` git-ignored), `docs/reviews/README.md` states that reviews are public, and `.gitignore` gained the two evaluation entries. No file is private, so T10 removes no paths for T7.

**Proposal (Claude, 2026-10-19).** None of these
documents contains client data, credentials or build values (checked by
reading them and by the guard). What they do contain is CVC's product plans
and internal usage figures, so the question for each is commercial, not
technical:

| Document(s) | What it reveals | Proposal |
|---|---|---|
| `docs/scope/master-project-document.md`, `clive-scope.md` | Product vision and roadmap (sales agent, tender agent, customer intelligence), the original working brief, hardware | **Public**; make it private only if the product roadmap is commercially sensitive |
| `docs/scope/scope-rev2.md`, `scope-rev3.md`, `docs/roadmap.md` | Technical phase plans | **Public** |
| `docs/PDDs/` (all five) | Phase designs; Phase 3B's planned security model (LAN-only, reverse proxy, roles) | **Public**: it describes controls, not gaps, and every service binds to localhost |
| `docs/course-correction-plan.md` | Workstreams and decisions | **Public** |
| `docs/sprints/course-correction/W2-docgen-value-check.md` | The interview plan (public), but T2 would write interview figures (document volumes and hours per type) to `docs/reviews/` | **Public after edits:** W2 T2's results go to `docs/simpro/private/` (or a new private store for business figures), not `docs/reviews/` |
| `docs/sprints/course-correction/W3-kb-audit.md` | Audit plan; the planned report holds KB counts and could name documents | **Public after edits:** the report may hold counts and pass/fail only; anything naming a document or customer goes to the private store |
| `docs/sprints/course-correction/W4-evaluation.md` | Plan for `evaluation/eval-set.yaml` and results, which would hold questions and expected answers taken from real documents | **Public after edits:** `eval-set.yaml` and `evaluation/results/` are client content, so they must be git-ignored (or kept in a private store); only the runner, the format and value-free summaries are tracked |
| `docs/recovery-plan.md` drill reports, `docs/STATUS.md` open risks | KB size and usage counts, disk wear, accepted operational risks | **Public** (low sensitivity; nothing is reachable from outside the host). Optional: replace the drill's usage counts with `<n>` |

The edits to W2–W4 change where future outputs are written. They take effect
before those tasks run, and there is nothing to remove from history today.

### T8 — Commit the HEAD changes

Commit T1–T7's changes on the branch (§13), as one commit per logical change.
Use the normal two-hop PR flow (feature → `develop` → `main`). **Stop point:**
both PRs merged, and `check-public-safe.py` exits 0 on `main` and `develop`.

**Accepted (Alex, 2026-10-20):** PRs #90 and #91 merged; `main` and `develop`
have identical content. `check-public-safe.py` exits 1 with 5 matches, all in
the two historical files T6 left to T10 ("replace in history only"), so the
exit-0 condition moves to T10's `--history` check on the rewritten mirror.

### T9 — Install gitleaks [needs approval: host package]

Install a pinned gitleaks release and run it on current HEAD
(`gitleaks dir . --redact`) as a second, independent ruleset. **Stop point:**
zero findings, or each finding classified in the private store.

**Run 2026-10-21 (Claude):** gitleaks 8.30.1 was already installed in the
user's `~/.local/bin`, so no host package was added. `gitleaks dir . --redact`
on the working tree: 0 findings, exit 0.

### T10 — Rewrite history in a mirror clone [destructive to SHAs; needs approval]

Never run this in the working repository.

1. Take the backup first:
   `git clone --mirror git@github.com:cvc-arus/CLIVE-I.git <scratch>/original.git`,
   then `git -C <scratch>/original.git bundle create <BACKUP_DIR>/clive-i-pre-public.bundle --all`.
2. Clone the mirror again to `<scratch>/public.git`, and run `git filter-repo`
   on it with:
   - `--invert-paths`: `.venv/`, `**/__pycache__/`, `*.egg-info/`, and the
     files marked private in T7;
   - `--replace-text` and `--replace-message` from
     `filter-repo-replacements.txt`, covering both file contents and commit
     messages;
   - `--mailmap` from `filter-repo-mailmap.txt` (D3).
3. In `public.git`, run:
   - `check-public-safe.py --history`: must exit 0;
   - `gitleaks git --redact`: must report 0;
   - a full offline test run on a checkout of the rewritten `main`.
4. Keep `.git/filter-repo/commit-map` (old SHA → new SHA) in the private store.

**Stop point:** all three checks pass; report counts only.

**Run 2026-10-20 (Claude, Alex's go-ahead), in the session scratchpad:**
- Backup: mirror of `origin` (3 branches, 91 `refs/pull`, 234 commits) and a
  verified bundle of all refs. The bundle is still in the scratchpad: Alex
  copies it to `BACKUP_DIR` (only `.env` holds the path).
- `public.git`: `refs/pull/*` dropped (GitHub's refs, not pushable to a new
  repository). Rewrite with `--invert-paths` on `.venv/`, `backups/`,
  `*/__pycache__/*` and `*.egg-info/*`; `--mailmap`; and blob and message
  callbacks calling the private `filter_repo_scrub.py`, which applies
  `filter-repo-replacements.txt` plus company-ID replacement inside the
  deny-list's company patterns. Deviations from step 2: callbacks instead of
  `--replace-text`/`--replace-message`, and `backups/`, which the plan did not
  list: history held one knowledge-base dump, added in the first commit and
  absent at HEAD. `refs/replace/*` (old hashes) deleted after the run.
- Result: 210 commits (92 merges), 3 branches. At `main` only the two T6
  historical files differ from the original; 174 files in both.
- `check-public-safe.py --history`: 0 matches in 1555 history objects, exit 0.
- `gitleaks git --redact`: 116 commits scanned, no leaks, exit 0.
- Offline suite on a checkout of rewritten `main`: 193 passed, 20 skipped,
  60 deselected, the same as the working repository. `ruff check` and
  `ruff format --check` pass.
- Commit map and ref map saved in the private store.
- Bundle copied to `BACKUP_DIR`; `git bundle verify` passes (Alex,
  2026-10-21).
- To be re-run (Alex, 2026-10-21) after this record and the clone-URL fixes
  in `README.md` and `docs/installation.md` (new repository `CLIVE.v2`) are
  merged, so the published history includes them. The local-only tag
  `phase2-complete` is not carried over.

**Re-run, as published (checked by Claude 2026-10-21 on a fresh mirror of
`CLIVE.v2`):** 213 commits, branches `main` and `develop`, no tags; `main`
includes PR #92 and the `develop` → `main` merge (PR #93).
`check-public-safe.py --history --repo <mirror>`: 0 matches in 1568 history
objects, exit 0. `gitleaks git --redact`: 117 commits scanned, no leaks,
exit 0. Against the old repository's `develop`, only the two T6 historical
files differ.

### T11 — [HUMAN] Create the new GitHub repository (D1)

Alex creates an **empty, private** repository on GitHub (no README, no
licence). Claude then pushes `main`, `develop` and tags from `public.git`
[needs approval: `git push`]. Alex clones it fresh and runs `check-public-safe.py
--history` on that clone. Alex switches the repository to **public** only after
it exits 0.

**Stop point:** Alex has flipped it to public.

**Done 2026-10-21 (Alex):** `cvc-arus/CLIVE.v2` created, pushed and switched
to **public**. The fresh-clone history check is the T10 re-run record above.

### T12 — Switch the working copy to the new history

1. Rename the current working directory to `CLIVE-I.pre-public` (archive; Alex
   deletes it later).
2. Clone the new repository to the original path, so the systemd unit's paths
   still work.
3. Copy over `.env` and `docs/simpro/private/` without reading them
   (`cp -a`), then run `uv sync`.
4. Run the offline suite and the mock integration suite.
5. Run one manual `scripts/backup.sh`.

**Stop point:** tests and the backup pass from the new clone.

**Done 2026-10-21 (Claude, Alex's go-ahead):**
- Old working directory renamed to `CLIVE-I.pre-public`; `CLIVE.v2` cloned to
  the original path with `develop` checked out.
- Copied with `cp -a`: `docs/simpro/private/` (mode 0700 kept),
  `deploy/smartd/smartd.conf.local`, `.vscode/`. `.env` is denied to Claude
  Code, so Alex copied it. Its `SIMPRO_TIMEOUT` line carried a stray `>`,
  which broke settings loading in the integration suite; Alex fixed it.
- Running containers were not touched: the Compose project name stays
  `clive-i`, and the only bind mount inside the repository is the tracked
  `configs/postgres/init-pgvector.sql`.
- From the new clone: `check-public-safe.py` 0 matches in 174 tracked files,
  exit 0 (T8's 5 matches are gone); offline suite 193 passed, 20 skipped,
  60 deselected; mock integration suite 59 passed, 1 skipped; `ruff check` and
  `ruff format --check` pass; `scripts/backup.sh` exit 0, `MANIFEST.txt` lists
  the private build notes (plain copy, D6). The installed systemd unit already
  points at the same path.

### T13 — [HUMAN] Retire the old GitHub copies (D2) — deferred

Per D2, the old private repository **stays** until everything has worked from
the new one, as judged by Alex: at minimum T12 passed and one scheduled backup
ran from the new clone. Until then:
- set it to **archived** (read-only) on GitHub, so nothing is pushed to it by
  mistake;
- it remains private and holds the only copy of PRs #1–#88.

When Alex decides, with the T10 bundle verified in the backup, Alex deletes
it. That removes every old commit, the PR refs and the PR texts, which are
outside git and can't be cleaned by a rewrite.

If the audit's rotation check showed a credential still in use, rotate it
before T11, not here.

**Stop point:** Alex confirms the archive. Deletion is a later, separate
confirmation.

### T14 — Documentation and status

- `docs/STATUS.md`: record the result.
- `docs/CHANGELOG.md`: add an entry.
- `docs/README.md`:
  - add index rows for this file, ADR-017,
    `docs/simpro/private-notes.template.md` and `scripts/check-public-safe.py`;
  - add a note that SHAs cited in documents written before the rewrite refer
    to the pre-publication history (map in the private store).
- `structure.txt`: regenerate it.

**Done 2026-10-21 (Claude):** `STATUS.md`, `CHANGELOG.md` and `docs/README.md`
updated. ADR-017 and `docs/simpro/private-notes.template.md` already had index
rows (T1, T2). `docs/README.md` indexes only documents, so the guard script
and the pre-rewrite SHA note are rules in its §2 rather than rows.
`structure.txt` regenerated.

## 4. Implementation

### 4.1 Why split, not ignore the whole `docs/simpro/`

Most of `docs/simpro/` describes how Simpro's public API behaves. That is
useful publicly and isn't secret. Only build-specific facts are sensitive, and
the audit found them in about 16 files, most of them outside `docs/simpro/`.
Ignoring a folder would leave those, break about 30 links, and drop the
documents from version control and backup.

### 4.2 Why the whole history, and why a new repository

- **History:** a public repository exposes every past commit, so cleaning HEAD
  alone isn't enough.
- **Why not rewrite in place and flip the existing repository to public:**
  - GitHub keeps rewritten-away commits reachable through `refs/pull/*` and
    its caches until GitHub Support purges them;
  - the 89 existing PR descriptions and comments would be published
    unchanged;
  - a fresh repository has neither problem.
- **Why not squash to a single commit:** that is simpler and equally safe, but
  it discards the history that `CHANGELOG.md` and verification evidence point
  to. Recommended only as the fallback if T10's checks can't reach zero.

### 4.3 Guard independence in the live test

Today the live test guards with a hardcoded ID set, independent of `.env`.
After T4 it uses two separate variables (`SIMPRO_COMPANY_ID_*` and
`SIMPRO_LIVE_COMPANY_IDS`), which must agree before anything runs.

- **Trade-off:** both now live in `.env`, so the guard is less independent
  than before, but a single typo still can't reach another company.
- **Rejected alternative:** reading the IDs from the private notes would couple
  a test to a Markdown file.

### 4.4 Decisions for Alex (T0)

| # | Question | Decision (Alex, 2026-10-19) |
|---|---|---|
| D1 | How to publish | **New repository** with the rewritten full history; fallback: a single squashed commit |
| D2 | Old private repository after T12 | **Keep** (archived, private) until everything works from the new one; deletion decided later (T13) |
| D3 | Commit author identity | **Rewrite** the human author's name to **Alex** and email to Alex's GitHub `noreply` address via mailmap |
| D4 | Project and owner names | **Keep "CVC"**; refer to the owner as **"Alex"** instead of the earlier short form |
| D5 | Business-context documents | Reviewed in T7: Claude proposes, Alex decides |
| D6 | Private notes in backup before GPG is set up | **Plain copy** in the 0700 backup folder for now |
| D7 | Licence | **Proprietary notice, all rights reserved** (option 1), copyright holder **CVC**; in place before T11 |

## 5. Commands

All are run from the repository root unless stated otherwise. No command
prints a sensitive value.

```bash
# T3 / T5 / T8
python3 scripts/check-public-safe.py              # tracked files
python3 scripts/check-public-safe.py --history    # all refs + messages

# T4
uv run pytest -q -m "not integration"
uv run pytest -m live --co -q
uv run ruff check . && uv run ruff format --check .

# T10 (in <scratch>, never in the working repo)
git clone --mirror git@github.com:cvc-arus/CLIVE-I.git original.git
git -C original.git bundle create "$BACKUP_DIR/clive-i-pre-public.bundle" --all
git clone --mirror original.git public.git
cd public.git && git filter-repo \
  --invert-paths --path .venv --path-glob '*/__pycache__/*' --path-glob '*.egg-info/*' \
  --replace-text <repo>/docs/simpro/private/filter-repo-replacements.txt \
  --replace-message <repo>/docs/simpro/private/filter-repo-replacements.txt \
  --mailmap <repo>/docs/simpro/private/filter-repo-mailmap.txt
gitleaks git --redact .
```

Private-file removal from T7 adds one `--path` argument per file; the T10
session confirms the exact flags (`git filter-repo --help`).

## 6. Configuration

| Variable | Change |
|---|---|
| `SIMPRO_COMPANY_ID_SERVICE`, `SIMPRO_COMPANY_ID_PROJECTS` | Live values only in `.env`; `.env.example` shows placeholders |
| `SIMPRO_LIVE_COMPANY_IDS` | **New**, test-only: the live test's allow-list (T4) |
| `BACKUP_DIR` | `.env.example` shows a placeholder |
| `BACKUP_GPG_RECIPIENT` | Unchanged; now also encrypts the private store (T2) |

## 7. Folder structure

```text
docs/simpro/
├── simpro-api-findings.md          tracked: Simpro's public API behaviour
├── mock-vs-public-api.md           tracked
├── private-notes.template.md       tracked: headings only
└── private/                        untracked, 0700, backed up
    ├── cvc-simpro-build.md
    ├── public-deny-list.txt
    ├── filter-repo-replacements.txt
    ├── filter-repo-mailmap.txt
    └── filter-repo-commit-map       (after T10)
docs/sprints/public-release/
└── public-release-split.md         this plan
scripts/check-public-safe.py        tracked guard
```

## 8. Files created / modified

- **Created:**
  - `docs/ADR/adr-017-public-repository-private-build-facts.md`
  - `docs/simpro/private-notes.template.md`
  - `scripts/check-public-safe.py`
  - this plan
- **Created, untracked:** everything under `docs/simpro/private/`, plus
  `deploy/smartd/smartd.conf.local`.
- **Modified:**
  - `.gitignore`, `.env.example`
  - `scripts/backup.sh`
  - `tests/test_live_contract.py`, `tests/test_pagination.py`
  - `deploy/smartd/smartd.conf`, `deploy/systemd/clive-backup.service`
  - the documents in T5, the approved ones in T6, `docs/ADR/ADR-index.md`,
    `docs/README.md`, `docs/STATUS.md`, `docs/CHANGELOG.md`
  - `structure.txt` (regenerated)

## 9. Verification

| Check | Expected |
|---|---|
| `python3 scripts/check-public-safe.py` on `main` and `develop` | exit 0, no output lines |
| `check-public-safe.py --history` on `public.git` and on a fresh clone of the new remote | exit 0 |
| `gitleaks git --redact` on `public.git` | 0 findings |
| `git check-ignore` on each private file | ignored |
| Offline suite, mock integration suite, ruff (whole repo) | pass |
| Live tests without opt-in | skipped |
| Manual `scripts/backup.sh` | `MANIFEST.txt` lists the private store |
| `/doc-check` | no new broken links |

Results are reported as counts and exit codes only.

## 10. Rollback procedure

- **T1–T8:** ordinary commits; revert the PRs.
- **T10:** works on copies only; delete `<scratch>`.
- **T11:** while still private, delete the new repository.
  - If it was flipped to public by mistake, make it private again at once.
    Treat anything pushed as exposed, and rotate credentials if the checks
    were bypassed.
- **T12:** rename `CLIVE-I.pre-public` back.
- **T13:** irreversible on GitHub. The T10 bundle is then the only full copy of
  the old history, so restore with `git clone <bundle>`. Don't start T13 until
  the bundle has been verified (`git bundle verify`).

## 11. Common issues

- **Replacement rules matching unrelated text.** Short numbers can occur
  elsewhere, so every rule is anchored to its context. Diff a sample of
  rewritten files before checking the deny-list.
- **`git filter-repo` refusing to run.** It requires a fresh clone. Re-clone
  rather than use `--force`.
- **Markdown code blocks.** `ruff format --check` inspects Python in Markdown,
  so code blocks edited in docs must keep it passing.
- **Old SHAs in documents.** Cited SHAs stop resolving after T10. That is
  expected; the commit map in the private store translates them.
- **Fresh clones have no deny-list.** The guard exits 2 rather than passing,
  and contributors without the private store are told why.
- **GitHub caches.** Search results and caches of the old repository can
  persist briefly after T13.

## 12. Documentation updates

`docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/README.md` (§3 state cells, new
index rows), `docs/ADR/ADR-index.md`, `docs/installation.md` §9,
`docs/recovery-plan.md` §7, and root `CLAUDE.md`: §2 points "Simpro facts" at
both files, and §3/§9 name variables instead of values.

## 13. Git commit

Branch (proposed, awaiting Alex): `chore/public-release-split`. Commits:

```text
docs(adr): propose ADR-017 (public repository, private build facts)
chore: add private build-notes store, public-safety check and ignore rules
chore: add proprietary licence notice
refactor(tests): read live company IDs from settings, not literals
docs: replace build-specific values with placeholders and variable names
```

T10–T13 produce no commits in this repository; they create the new history
and remote.

## 14. Acceptance criteria

- [x] `check-public-safe.py --history` exits 0 on a fresh clone of the published repository
- [x] gitleaks reports 0 findings on the published history
- [x] No tracked file contains a value listed in the private deny-list
- [x] `docs/simpro/private/` is ignored, backed up, and listed in the recovery plan
- [x] `.env.example` holds placeholders for every value moved to `.env`
- [ ] The live test refuses to run unless both company-ID variables agree, and blocks every other company route
- [x] Offline suite, mock integration suite and whole-repo ruff pass from the new clone
- [ ] The old GitHub repository is deleted or archived per D2, and the pre-public bundle is verified in backup
- [x] A proprietary `LICENSE` approved by Alex is in the published repository, and both `pyproject.toml` files declare it
- [x] No tracked file or commit message in the published history refers to the owner by the earlier short form
- [x] ADR-017 accepted by Alex; STATUS, CHANGELOG and README updated
