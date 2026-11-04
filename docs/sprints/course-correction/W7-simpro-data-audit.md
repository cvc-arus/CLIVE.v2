# W7 — Simpro Data-Quality Audit

| | |
|---|---|
| **Template** | Short (read-only against Simpro; results go to the untracked private store) |
| **Status** | Approved (Alex, 2026-11-03) |
| **Depends on** | W1 T5 (live contract tests pass, so the client reads live payloads) |
| **Related** | ADR-009 (live tests are the only non-gateway importer), ADR-013, ADR-016 (`columns`), ADR-017 (private store), `tests/test_live_contract.py`, `docs/simpro/simpro-api-findings.md` |

## Goal

CVC's Simpro data has quality problems: duplicate sites, sites with no customer
or no assets, and similar. This workstream builds opt-in, read-only live tests
that find them, and writes every finding to a report Alex can act on. CLIVE's
later query catalogue (ADR-015) is only as good as this data.

Decisions (Alex, 2026-11-03):

- The report goes to `docs/simpro/private/data-audit/<YYYY-MM-DD>/`. That folder
  is untracked (`.gitignore` covers `docs/simpro/private/`), and **results never
  reach git**.
- **Claude Code never reads the report.** It holds customer data (root
  `CLAUDE.md` §9). Terminal output is limited to check IDs, counts and pass/fail.
- All assets are scanned: one GET per site, about 6,500 requests, about 15 minutes.
- Postcodes are validated against the UK format.
- S7 ("dormant site") means no jobs and no quotes ever.

Nothing is written to Simpro. Fixing the data is Alex's job, in Simpro (T4).

## Design

- **Live module:** `tests/test_live_data_quality.py`, marked `live`. It runs
  only when both `SIMPRO_LIVE_TESTS=1` and `SIMPRO_DATA_AUDIT=1` are set, so
  the plain live contract run never starts the scan. Each check is one test
  that fails when it has findings. The failure message is only
  `<check id>: <n> findings`.
- **Check logic:** pure functions in `tests/simpro_data_checks.py` (a helper
  module, not collected). They are tested offline in
  `tests/test_simpro_data_checks.py` on synthetic records. No new dependency:
  normalisation and fuzzy matching use the standard library only.
- **Safety rails, as in `test_live_contract.py`:**
  - GET only.
  - The request hook rejects any company outside `SIMPRO_LIVE_COMPANY_IDS`.
  - `simpro_client` logging is disabled.
  - Run with `--tb=no -rN`.
  - `request_guard` moves to `tests/conftest.py`, because two modules now
    use it (`tests/CLAUDE.md` §3).
- **Report safety:**
  - Before writing anything, the module runs `git check-ignore` on the report
    directory and aborts if the directory is not ignored.
  - Directory mode is 0700 and file mode 0600.
  - Custom fields, notes and amounts are never requested (`columns`), so they
    cannot be written.
- **Guard against Claude Code reading the report:** a `deny` rule for
  `docs/simpro/private/data-audit/**` in `.claude/settings.json`.

### Data fetched

| Data | How | Requests |
|---|---|---|
| Sites (build-wide) | The service company; `columns` ID, Name, Address, Customers, PrimaryContact, Archived | ~26 |
| Site IDs in the projects company | ID-only projection; checks the "build-wide" assumption (findings §2.3) | ~26 |
| Company and individual customers | `columns` incl. Sites, Contacts, Email, Phone, Archived | ~15 |
| `/customers/` summary | Total only | 1 |
| Jobs and quotes, both companies | `columns` ID, Site, Customer, Stage, dates | ~115 |
| Assets | One request per site (the only route there is); `columns` exclude `CustomFields` | ~6,500 |

### Checks

| ID | Records | Finding |
|---|---|---|
| S1 | Site | No customer |
| S2 | Site | Links to a customer that doesn't exist, or to an archived customer |
| S3a | Site | Duplicate: same normalised name and address |
| S3b | Site | Likely duplicate: same normalised address, different name (shared buildings land here for review) |
| S3c | Site | Possible duplicate: similar name, different address (fuzzy) |
| S4 | Site | No assets |
| S5a | Site | Address incomplete: street, city or postcode blank |
| S5b | Site | Postcode not in valid UK format |
| S5c | Site | Country set and not UK; postcode format not checked, listed for review |
| S6 | Site | Name blank, or a placeholder (`test`, `tbc`, `-`, `unknown`, `do not use`, …) |
| S7 | Site | Not archived, and has no jobs and no quotes ever |
| S8 | Site | No primary contact |
| S9 | Site | More than one customer (allowed in Simpro; for review) |
| S10 | Site | Archived, but has open jobs or quotes |
| C1 | Customer | No sites |
| C2 | Customer | No contacts |
| C3 | Customer | Duplicates. Companies: normalised name (Ltd/Limited, `&`/`and`, punctuation). Individuals: name plus email or phone |
| C4 | Customer | The same email or phone on different customers |
| C5 | Customer | No email and no phone |
| C6 | Customer | Required name blank or whitespace |
| C7 | Customer | Badly formed email |
| C8 | Customer | Archived, but has active sites or open jobs |
| C9 | Customer | Summary total ≠ companies + individuals; an ID in both subtypes or in neither |
| CT1 | Contact | Duplicate within one customer |
| CT2 | Contact | Blank name |
| A1 | Asset | `ParentID` points to an asset that is not on the same site |
| A2 | Asset | Active asset on an archived site |
| J1 / Q1 | Job / quote | Site missing or not found; customer missing |
| J2 / Q2 | Job / quote | Customer is not one of its site's customers |
| X1 | Run | Site ID sets differ between the two companies |

Contact checks use only what the customer's `Contacts` list returns (IDs and
names). Checking contact email and phone would need about 3,000 more requests,
one per contact. That is out of scope.

### Edge cases (each is covered by an offline test in T1)

1. **Projection silently ignored.** If a requested key is *absent* from the
   payload, the dependent checks abort with an error rather than report every
   row. A key that is present but empty is a finding.
2. **Blank values.** `null`, `""`, whitespace only and non-breaking spaces all
   count as blank.
3. **Two blank addresses are never a duplicate match.**
4. **Unit and flat numbers stay in the address key.** "Unit 1, 5 High St" is not
   a duplicate of "Unit 2, 5 High St".
5. **Normalisation:** case, accents, punctuation and repeated spaces, plus
   conservative abbreviation folding (St/Street, Rd/Road, Ave/Avenue,
   Ltd/Limited). Fuzzy matches go only to S3c, never to S3a.
6. **UK postcodes:**
   - Accepted regardless of case and of a missing or doubled space.
   - `GIR 0AA` is valid.
   - BT, JE, GY and IM postcodes are valid.
   - BFPO and partial postcodes (outward code only) are invalid.
   - A UK country value is recognised in any of these forms: UK, GB, United
     Kingdom, England, Scotland, Wales, Northern Ireland.
7. **Archived records** are included and flagged in their own column, never
   dropped or mixed in silently.
8. **Data changing during the run.**
   - `Result-Total` is recorded at the start and the end, and any drift is
     reported in the summary.
   - Rows are de-duplicated by ID, because offset paging can shift. Repeated
     IDs are counted.
9. **Run failing partway** (429, token expiry, network): `summary.md` is
   stamped `INCOMPLETE` and the run fails. A partial run is never reported as
   clean.
10. **Validation errors** are recorded by field location only, never by value.
11. **Output is deterministic:** rows are sorted by ID, so two runs can be diffed.
12. **Duplicate groups:** each group has a group ID, so all its members appear
    together. Groups of one are never reported.

### Report layout

`docs/simpro/private/data-audit/<YYYY-MM-DD>/`:

- `summary.md`: run start and end, request count, totals and drift, and a
  count for each check.
- `<check id>.csv`: one file per check, holding record IDs, the fields needed
  to act on the record, and the reason.

## Tasks

### T1 — Check logic and offline tests
1. Write `tests/simpro_data_checks.py`: normalisation, the UK postcode
   validator, and one pure function per check, taking plain records and
   returning findings.
2. Write `tests/test_simpro_data_checks.py`. Every edge case above gets a
   parametrized test on synthetic data.
3. Run the offline suite and ruff on the new files.

**Stop point:** report test counts and lint results; propose a commit.

### T2 — Live module (do not run it in this task)
1. Move `request_guard` to `tests/conftest.py`, and update
   `test_live_contract.py` to import it. No other change to that module.
2. Write `tests/test_live_data_quality.py`:
   - the double opt-in;
   - a pre-flight projection test, run first (1-row page per projection;
     reports missing field *names* only);
   - fetching, which writes nothing to stdout;
   - the `git check-ignore` guard;
   - the report writer;
   - one test per check.
3. Add the read-deny rule for `docs/simpro/private/data-audit/**` to
   `.claude/settings.json`.
4. Confirm that the default run and `SIMPRO_LIVE_TESTS=1` without
   `SIMPRO_DATA_AUDIT=1` make no audit requests: the audit tests skip.

**Stop point:** offline suite and lint results; propose a commit.

### T3 — Run the audit (only when Alex asks)

```bash
COLUMNS=200 SIMPRO_LIVE_TESTS=1 SIMPRO_DATA_AUDIT=1 uv run pytest tests/test_live_data_quality.py -m live -v --tb=no -rfE
```

Report pass or fail and the count for each check. Confirm that
`git status --porcelain` shows nothing under `docs/simpro/private/`.
Do **not** open the report.

**Stop point:** counts reported to Alex.

### T4 — [HUMAN] Review and fix
Alex reviews the CSVs and fixes the records in Simpro. CLIVE never writes to
Simpro. Re-run T3 to measure progress.

### T5 — Documentation
- `tests/CLAUDE.md` §1: add the audit layer and its command.
- `docs/simpro/simpro-api-findings.md`: the method and request budget only;
  no values or counts of client records beyond what is already public.
- This file's Status.
- `docs/STATUS.md`, and its `docs/README.md` row.

**Stop point:** propose a commit.

## Verification
- `uv run pytest -q -m "not integration"`: all pass, with the new offline tests
  included.
- `uv run ruff check .` and `uv run ruff format --check .`: pass.
- `python3 scripts/check-public-safe.py` exits 0 on the changed files.
- `git status --porcelain --ignored docs/simpro/private/`: report files show as
  ignored (`!!`) only.

## Rollback
Run `git revert <commit>`. The untracked report folder can be deleted by Alex
by hand.

## Git commit
- T1: `test(simpro): data-quality check logic with offline edge-case tests`
- T2: `feat(tests): opt-in live Simpro data-quality audit to private store`
- T5: `docs(simpro): record W7 data-quality audit`

## Acceptance criteria
- [ ] Every edge case listed has an offline test, and the offline suite passes.
- [ ] The default run and the plain live run make no audit requests.
- [ ] Live output contains only check IDs, counts and pass/fail.
- [ ] Only GET requests and the token request are sent, and only to the two
      configured companies.
- [ ] The report exists only under `docs/simpro/private/data-audit/`, is
      git-ignored, and was never read by Claude Code.
- [ ] `docs/STATUS.md` updated.
