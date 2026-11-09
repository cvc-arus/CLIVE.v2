# CLIVE — Status

> Single source of truth for current status. Update after every completed task
> (`/status-update`). Keep this file short: history belongs in `docs/CHANGELOG.md`,
> decisions in `docs/ADR/`.

**Last updated:** 2026-11-09

## Phases

Phase list and scope: `docs/roadmap.md`.

| Phase | Name | Status |
|---|---|---|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG | ✅ Complete. Knowledge base audit (W3) done; option B accepted, bulk ingestion paused until its conditions are met |
| 3 | Simpro API Integration | ✅ Closed 2026-10-09 (Alex). Evidence: `docs/phase3/phase3-signoff.md` |
| — | Course correction sprint | 🔶 In progress — resumed 2026-10-21 (Alex) after the public-release sprint |
| — | Public-release sprint | ✅ Complete 2026-10-21 (Alex): `docs/sprints/public-release/public-release-split.md`. The rewritten history is the **public** repository `cvc-arus/CLIVE.v2`; `check-public-safe.py --history` and gitleaks are clean on it; the working copy is a clone of it. The old `cvc-arus/CLIVE-I` is archived and private; deleting it is Alex's later decision (D2) |
| — | Dependency security fixes | ✅ Complete 2026-11-09: certifi, python-dotenv, python-multipart and Mako updated (PRs #44, #45); live contract tests 25/25 with the new CA bundle; 0 open Dependabot alerts (13 fixed). Plan: `docs/sprints/dependency-security/dependency-security-fixes.md` |
| 3B | Simpro Conversational Access | 📝 Planned — PDD drafted; ADR-014 and ADR-015 accepted 2026-11-03 (Alex); order set at decision point |
| 4 | Document Generation (4A / 4B split proposed by W2; decided at the decision point) | ⏳ Not started; no longer blocked (ADR-009 decided) |
| 5 | Security & Reverse Proxy (minimum slice moves into 3B) | ⏳ Not started |
| 6–9 | Sales Agent, Tender Agent, Customer Intelligence, Multi-Agent | ⏳ Not started |
| 10 | Monitoring & Disaster Recovery (backups moved to W5) | ⏳ Not started |

## Current sprint: Course correction

Plan: `docs/course-correction-plan.md` · Tasks: `docs/sprints/course-correction/`

| Workstream | Status | Notes |
|---|---|---|
| W1 Simpro access and live API checks | ✅ Complete 2026-11-04 (signed off by Alex) | Live API access arrived 2026-10-16; read-only use (root `CLAUDE.md` §3, §9); only the two configured companies. T1 not needed (Alex). T2: `docs/simpro/mock-vs-public-api.md`. Live smoke check 2026-10-17 (§6): 3 differences broke the client. T4: all three fixed — `/companies/` paging, `""` dates, and `ID` in projections under ADR-016 (accepted by Alex 2026-10-19); merged to `main` 2026-10-19 (PRs #86, #87). T3: opt-in live tests merged, skipped by default (`SIMPRO_LIVE_TESTS=1`). T5 done 2026-11-03 (§7): 25/25 pass after a header-case test fix (PRs #18, #19); `expires_in` 3600 confirmed; a new token did not revoke the old one; `_href` accepted as a column. ADR-015 live filter checks (§8): customer, site, staff and `%` text filters work; unknown filter fields are ignored. Rate limit not measured. All acceptance criteria met |
| W2 Doc generation value check | ✅ Complete 2026-11-04 | T1 run as a written survey (5 responses; figures in the private store). Ranking: quotes, technical documents, tender responses, method statements, RAMS; contracts not produced. Proposed split: 4A = technical documents, tenders, method statements, RAMS; 4B = quotes. `docs/reviews/doc-generation-value-check.md` |
| W3 Knowledge base audit | ✅ Complete 2026-11-05 (Alex) | Report: `docs/reviews/kb-audit-2026-10.md` §1–§4. Decision (Alex, 2026-11-05): **option B**, ingestion conventions over Open WebUI's API (metadata plus `doc_id`/`version` on every upload, collections by document family and sensitivity with group grants, superseded versions in an admin-only archive, model rows and groups so regular users can chat). **Bulk ingestion stays paused** until (1) Alex approves B's field list and collection layout, (2) the ingestion script is built and tested on synthetic documents, (3) model rows and groups exist, (4) scanned PDFs and drawings are spot-checked. Option C (own pipeline) only if W4 shows metadata filtering matters |
| W4 Evaluation set | 🔶 In progress | T1 design approved by Alex 2026-11-04 (`evaluation/README.md`). T2 done by Alex 2026-11-05: 40 questions (24 lookup, 10 multi_doc, 6 not_found) in the git-ignored `evaluation/eval-set.yaml`; 33 of 34 answerable facts are present in the extracted text (W3 §3.2). T3 done 2026-11-06: `scripts/eval/run_eval.py` (`EVAL_*` settings, `PyYAML` in the dev group, results git-ignored and backed up); dry run on 3 questions: 3/3 answered, expected sources cited, but 0/4 expected facts in the answers. The facts are in the extracted text; retrieval (top-k, no reranker, a combined datasheet duplicating single ones) does not return the chunks that hold them, so reranking and the collection layout belong in option B. A thinking model returned empty answers until thinking was turned off; the runner now records empty answers as errors. 4 source groups (L07, L08, L09, M06) name files not in the collection. T4 baseline waits for option B's conditions 1–3 (W3 row) |
| W5 Backups and restore drill | ✅ Complete 2026-10-16 | Closed by Alex with T7 recorded as an accepted risk (Open risks). T1: all data on sdb1; target `BACKUP_DIR` (sda2). T2: inventory agreed. T3: `scripts/backup.sh` backs up the full inventory except `.env` (GPG key deferred). T4: daily systemd timer at 02:30 installed. T5: `smartd` monitoring both disks; both are past their rated write endurance (recovery plan §9). T6: restore drill passed, about 68 s of commands from checksums to a working Open WebUI (recovery plan §10). T7 (off-machine copy) not done: accepted risk. See `docs/recovery-plan.md` |
| W6 Docs consolidation | ✅ Complete 2026-10-15 | Accepted by Alex. `STATUS.md` owns status; Phase 3 evidence in `phase3/phase3-signoff.md`; ADR index conventions merged; Simpro findings applied to Phase 3B; root `CLAUDE.md` additions merged and `/sprint-task`, `/status-update` confirmed; `PDD-phase3.md` revised and closed; `docs/reviews/` created. Security documentation deferred to Phase 3B Sprint 2 |
| W7 Simpro data-quality audit | ✅ Closed 2026-11-04 (Alex) | Opt-in, read-only audit (`tests/test_live_data_quality.py`, double opt-in); run by Alex; findings only in the git-ignored private store, never read by Claude Code. Fixing the records is Alex's work in Simpro (T4), outside CLIVE |

**Next task:** scope option B as its own task: Alex approves the field list and collection layout first; scanned-PDF and drawing spot-check (D1) alongside. W4 T4 baseline after B's conditions 1–3.
**Next decision:** phase order, at end of sprint.

## Simpro access

| Item | Status |
|---|---|
| Live API access | ✅ Granted 2026-10-16, free. OAuth2 Client Credentials; credentials in `.env` (Alex); application checked with Postman (Alex). Read-only use only. Live read-only smoke check run 2026-10-17 (`docs/simpro/mock-vs-public-api.md` §6); live contract tests and ADR-015 filter checks run 2026-11-03 (§7, §8) |
| Shared sandbox | Not used (Alex, 2026-10-16) |
| Company IDs (Service, Projects) | Recorded (Alex, 2026-10-16) in `.env` and the private build notes (ADR-017). The build lists other companies too: listing `/companies/` is allowed, but no request is sent to any other company (Alex, 2026-10-17) |

## Open risks

| Risk | Status |
|---|---|
| No off-machine backup — accepted until the off-machine copy is in place (Alex, 2026-10-16; no end date set) | Open — deferred until production (Alex, 2026-10-21). W5 closed without T7; target not yet chosen. Cross-disk backups do not cover theft, fire, `rm` or ransomware (`docs/recovery-plan.md` §11) |
| Both SSDs are past their rated write endurance (129 % and 116 %), from the same batch, so both could fail close together | Open — deferred until production (Alex, 2026-10-21): replace both, `sdb` first; firmware update to be looked into (Alex, 2026-10-14). See `docs/recovery-plan.md` §9 |
| Knowledge base does not yet meet the metadata, versioning and access requirements (W3 §4.1) | Mitigation decided (Alex, 2026-11-05): option B; bulk ingestion paused until its four conditions are met (W3 row) |
| Simpro's API application has no dedicated read-only security group: Simpro does not stop CLIVE writing, and a leaked client secret could write (detail in the private build notes, ADR-017) | Open (Alex, 2026-10-16). Guards are the read-only rule (root `CLAUDE.md` §3) and the GET-only client. See `docs/simpro/simpro-api-findings.md` §2.2 |
| Simpro rate limit not confirmed | Open — public docs give 10 req/s per build; conservative defaults kept (ADR-010, ADR-012); not measured in W1 T5. Token lifetime confirmed live 2026-11-03 (3600 s; a new token did not revoke the old one, `docs/simpro/mock-vs-public-api.md` §7) |
| `.env` is not backed up until the GPG key pair exists; until then the private build notes are a plain copy in the 0700 backup folder (ADR-017, D6) | Open — deferred until production (Alex, 2026-10-21) |
| Open WebUI's signing key (`WEBUI_SECRET_KEY`) is generated inside the container, not backed up: a restore or container rebuild logs everyone out | Open — deferred until production (Alex, 2026-10-21); fix needs `WEBUI_SECRET_KEY` in `.env` and Compose. See `docs/recovery-plan.md` §10 |
| A git identity on the private deny list (ADR-017) is in the author/committer fields of 61 public commits (2026-10-21 to 2026-11-05), found by `check-public-safe.py --history` on 2026-11-05; file contents are clean and gitleaks finds no leaks | Accepted (Alex, 2026-11-05): history not rewritten, since the commits have been public for two weeks. The repository's local git identity now uses the GitHub no-reply address, and Alex turned on GitHub's "Keep my email addresses private", so web merges use it too (checked on PRs #38–#39); merge commits still show the account handle as author name. Repository secret scanning and push protection enabled 2026-11-06 (Alex; confirmed through the GitHub API, 0 alerts) |

## ADRs awaiting a decision

None. ADR-014 and ADR-015 accepted 2026-11-03 (Alex).
