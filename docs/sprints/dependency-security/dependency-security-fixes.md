# Dependency security fixes (Dependabot, 2026-11)

> **Full template**: this changes security-relevant dependencies of the client
> library and the mock image.

| | |
|---|---|
| **Status** | Approved by Alex 2026-11-06 |
| **Depends on** | Nothing |
| **Related ADRs** | ADR-004 (httpx), ADR-007 (pydantic-settings). No new ADR: version updates of packages already in use, no new dependency or category |

## 1. Goal

Close the 13 open Dependabot alerts on `cvc-arus/CLIVE.v2` (found 2026-11-06,
when secret scanning and push protection were enabled). They come from four
packages:

| Package | Lock file / pin | Locked → fixed | Advisory | Impact for CLIVE |
|---|---|---|---|---|
| `certifi` (transitive, via `httpx`) | `uv.lock`, `services/simpro_mock/uv.lock` | 2026.7.22 → 2026.10.18 | GHSA-6q48-6c7w-9gw2 (critical): bundled emSign roots with compromised intermediate CA keys | **Real.** `httpx` verifies TLS with `certifi.where()`, so `simpro_client`'s live calls to `*.simprosuite.com`, including the token request with the client secret, would trust a certificate forged under those keys |
| `python-dotenv` | `pyproject.toml` `==1.1.0` | 1.1.0 → 1.2.3 | GHSA-mf9w-mj56-hr94 (medium): symlink following in `set_key` | Low. CLIVE never calls `set_key`; pydantic-settings only reads `.env`. The mock already locks 1.2.3 |
| `python-multipart` | `services/simpro_mock/pyproject.toml` `==0.0.27` | 0.0.27 → 0.0.31 | GHSA-5rvq-cxj2-64vf (high), GHSA-v9pg-7xvm-68hf, GHSA-6jv3-5f52-599m, GHSA-vffw-93wf-4j4q (low) | Low. Parses the mock's `/oauth2/token` form; the mock is development-only, holds no real data and binds to `127.0.0.1:8100` |
| `Mako` (transitive, via Alembic) | `services/simpro_mock/uv.lock` | 1.4.1 → 1.4.2 | GHSA-5639-2j2p-m4mx (medium): Windows drive-letter path traversal | None on Ubuntu; updated to clear the alert |

## 2. Business value

The live Simpro credentials can write to CVC's build (open risk in
`docs/STATUS.md`), so the TLS check that protects them must not trust
compromised CAs. Clearing the low-impact alerts as well keeps the Dependabot
list at zero, so a new alert stands out.

## 3. Tasks

### T1 — Root project (`simpro_client`)
1. `pyproject.toml`: `python-dotenv==1.1.0` → `python-dotenv==1.2.3`.
2. Re-lock, upgrading `certifi` only:
   `uv lock --upgrade-package certifi --upgrade-package python-dotenv`.
3. `uv sync`; confirm the locked versions (§9).
4. Offline suite and whole-repo lint.
**Stop point:** versions confirmed, offline suite and lint pass.

### T2 — Mock (`services/simpro_mock/`)
1. `services/simpro_mock/pyproject.toml`: `python-multipart==0.0.27` →
   `python-multipart==0.0.31`.
2. Re-lock in `services/simpro_mock/`:
   `uv lock --upgrade-package certifi --upgrade-package mako --upgrade-package python-multipart`.
3. Rebuild the mock (`docker compose up -d --build simpro-mock`; the image runs
   `uv sync --locked`, so it picks up the new lock) and run the integration
   tests.
**Stop point:** mock healthy, integration tests pass.

### T3 — [HUMAN] Live TLS check (Alex)
Only when Alex asks: run the opt-in live contract tests, which make the token
`POST` and read-only `GET`s, to confirm TLS to `*.simprosuite.com` verifies
with the new CA bundle:
`SIMPRO_LIVE_TESTS=1 uv run pytest -m live -v --tb=no -rN`.
**Stop point:** pass count reported (no values).

### T4 — Close-out
1. Confirm the Dependabot alerts closed after the merge to `main`.
2. Documentation updates (§12); remove the open-risk row.
**Stop point:** zero open Dependabot alerts; report for Alex's sign-off.

## 4. Implementation

- **Why `--upgrade-package` rather than `uv lock --upgrade`:** only the
  flagged packages move, so a test failure points at one of them, and no
  unrelated pins drift. Root `CLAUDE.md` §7 requires exact pins; the two
  direct dependencies stay `==`, and the transitive ones are pinned by the
  lock files.
- **`python-dotenv` 1.2.3 rather than the minimum 1.2.2:** the mock already
  runs 1.2.3 with pydantic-settings, so both projects use one known version.
- **`certifi` removes trust in the emSign roots.** If Simpro's certificate
  chained to one of them, TLS to Simpro would fail after the update; that is
  the intended outcome of the fix and T3 detects it. Simpro's chain is not
  expected to use emSign.
- **No live call until T3.** Until the fix is merged, live Simpro runs are
  avoided (open risk in `docs/STATUS.md`).
- The two projects stay independent (root `CLAUDE.md` §3): each lock file is
  changed in its own directory.

## 5. Commands

```bash
# T1 (repo root)
uv lock --upgrade-package certifi --upgrade-package python-dotenv
uv sync
uv run pytest -q -m "not integration"
uv run ruff check . && uv run ruff format --check .

# T2
cd services/simpro_mock
uv lock --upgrade-package certifi --upgrade-package mako --upgrade-package python-multipart
cd ../..
docker compose up -d --build simpro-mock
uv run pytest -m integration -v --tb=no

# T4 (after the merge to main)
gh api 'repos/cvc-arus/CLIVE.v2/dependabot/alerts?state=open' --jq length
```

## 6. Configuration

None. No `.env` variable is added or changed.

## 7. Folder structure

Unchanged.

## 8. Files created / modified

| File | Change |
|---|---|
| `pyproject.toml` | `python-dotenv` pin |
| `uv.lock` | `certifi`, `python-dotenv` |
| `services/simpro_mock/pyproject.toml` | `python-multipart` pin |
| `services/simpro_mock/uv.lock` | `certifi`, `Mako`, `python-multipart` |
| `docs/STATUS.md`, `docs/CHANGELOG.md`, `docs/README.md` | §12 |

## 9. Verification

| Check | Expected |
|---|---|
| `uv run python -c "import certifi, dotenv; print(certifi.__version__)"` and `uv pip show python-dotenv` | certifi ≥ 2026.10.18, python-dotenv 1.2.3 |
| Locked versions in `services/simpro_mock/uv.lock` | certifi ≥ 2026.10.18, Mako ≥ 1.4.2, python-multipart 0.0.31 |
| `uv run pytest -q -m "not integration"` | Same pass count as before the change, no failures |
| `uv run ruff check .`, `uv run ruff format --check .` | Pass |
| `uv run pytest -m integration -v --tb=no` (mock rebuilt) | All pass, including the `/oauth2/token` form tests |
| `python3 scripts/check-public-safe.py` (and `--history` before pushing) | 0 in the tree; history count grows only by merge-commit hits |
| T3 live run (Alex) | All live tests pass |
| Open Dependabot alerts after the merge to `main` | 0 |

## 10. Rollback procedure

`git revert` the commit, then `uv sync` at the root and
`docker compose up -d --build simpro-mock`. No data or volumes change.

## 11. Common issues

- **`python-multipart` 0.0.31 behaviour changes** (semicolon no longer a field
  separator, stricter `Content-Length`): the mock's token form uses `&`, so no
  change is expected; the integration tests confirm it.
- **TLS failure in T3** (`CERTIFICATE_VERIFY_FAILED`): Simpro's chain uses a
  root the new bundle no longer trusts. Stop and report; do not pin the old
  `certifi`.
- **Bytecode or `egg-info` files appear modified after the tests**: restore
  them with `git checkout -- <path>`; never stage them (root `CLAUDE.md` §8).

## 12. Documentation updates

- `docs/STATUS.md`: remove the Dependabot open-risk row; record the result.
- `docs/CHANGELOG.md`: entry with the four packages and versions.
- `docs/README.md`: "Current state" cells for the changed living documents.

## 13. Git commit

`fix(deps): update certifi, python-dotenv, python-multipart and Mako for Dependabot alerts`

## 14. Acceptance criteria

- [ ] Root lock: certifi ≥ 2026.10.18, python-dotenv 1.2.3
- [ ] Mock lock: certifi ≥ 2026.10.18, Mako ≥ 1.4.2, python-multipart 0.0.31
- [ ] Offline suite and whole-repo lint pass
- [ ] Mock rebuilt; integration tests pass
- [ ] Live TLS check passed (T3, Alex)
- [ ] Zero open Dependabot alerts on `main`
- [ ] `STATUS.md`, CHANGELOG and `docs/README.md` updated
