# ADR-017: Public repository, private build facts

- **Status:** **Accepted** — 2026-10-19 (Alex). Drafted by Claude for the
  public-release sprint (`docs/sprints/public-release/public-release-split.md`
  T1); proposed and accepted the same day.
- **Date:** 2026-10-19
- **Deciders:** Alex
- **Related:** root `CLAUDE.md` §2, §3 and §9; ADR-006 (no CLIVE specifics in
  `simpro_client`); ADR-014 (access control model); `scripts/backup.sh` and
  `docs/recovery-plan.md`.

## Context

Alex wants the CLIVE repository to be public. A privacy audit on 2026-10-19
found:

- **No client data and no live credential** in the working tree, the history
  or the unreachable objects.
- **Facts specific to CVC's Simpro build** in about 16 tracked files: the
  company IDs in use, the other companies in the build, the API application's
  permission level, the environment type and live-check specifics.
- **Host details:** disk IDs, home paths, a container IP and the developer's
  email.
- **One old mock-database password** in history.

These facts are harmless in a private repository. In a public one they tell an
attacker which tenants to aim at and what a leaked credential could do.

Three constraints shape the decision:

- **Some of the facts are binding rules.** For example, "only the two configured
  companies are ever queried" and "never write, whatever the credentials
  permit" must stay in force for Claude Code and for tests.
- **A public repository exposes its whole history**, not just HEAD.
- **GitHub keeps more than git does.** Pull-request texts live outside git,
  and rewritten-away commits stay reachable through `refs/pull/*` until GitHub
  purges them.

## Alternatives Considered

| Option | Summary | Verdict |
|---|---|---|
| A. Stay private | No change | Rejected: Alex wants a public repository |
| B. Ignore `docs/simpro/` in git | Hide the folder that holds most findings | Rejected. It misses the facts in about 14 other files, leaves history untouched, breaks about 30 links, and drops the documents from version control and backup |
| C. Split, guard, rewrite, publish to a new repository | Build facts move to an untracked, backed-up private store or `.env`. Tracked files use placeholders and variable names. A guard script blocks regressions. History is rewritten and pushed to a new repository | **Recommended** |
| D. As C, but publish a single squashed commit | Simplest guarantee of a clean history | Fallback if C's checks can't reach zero; loses the history that `CHANGELOG.md` and verification evidence cite |
| E. As C, but rewrite in place and make the existing repository public | Keeps the URL and PRs | Rejected: publishes 89 PR descriptions and comments unchanged, and old commits stay reachable through PR refs |

## Decision

1. **No build- or host-specific values in tracked files.** That covers Simpro
   company IDs, the other companies in the build, the API application's
   permission level, the environment type, live-check specifics, disk IDs,
   home paths, internal IPs and personal emails. Tracked files name the
   variable or link to the private store.
2. **Where those values live:**
   - **Configuration values** go in `.env`, with a placeholder in
     `.env.example`.
   - **Facts** go in `docs/simpro/private/`, which is git-ignored, mode 0700,
     and backed up by `scripts/backup.sh` (plain copy in the 0700 backup
     folder until a GPG recipient is set, then encrypted).
   - A tracked `docs/simpro/private-notes.template.md` lists what the store
     must contain.
3. **Rules stay tracked; values do not.** Root `CLAUDE.md` keeps every rule
   (only the configured companies, GET-only, no writes) and points to the
   private store for the values. Claude Code may read the private store; it
   still never reads `.env`.
4. **A guard enforces it.** `scripts/check-public-safe.py` checks tracked
   files, or with `--history` all reachable blobs and commit messages, against
   `docs/simpro/private/public-deny-list.txt`. It prints only path, line and
   pattern ID, exits 1 on a hit and exits 2 if the deny-list is missing.
5. **Publication:**
   - The history is rewritten with `git filter-repo` in a mirror clone.
     Build artefacts are removed, values replaced, and the human author's
     name and email mapped to Alex's GitHub `noreply` identity.
   - The result is pushed to a **new** repository, which is made public only
     after a fresh clone passes the guard and gitleaks.
   - The old repository stays private and archived until Alex retires it.
6. **Licence:** the published repository carries a proprietary "all rights
   reserved" notice, copyright CVC.

## Consequences

- **A fresh clone lacks the private store.** Live tests skip and the guard
  exits 2 until the store is restored from backup or filled in from the
  template.
- **The live test's company allow-list moves from a literal in the test to
  `SIMPRO_LIVE_COMPANY_IDS`**, which must equal the configured company IDs.
  The guard is slightly less independent than a literal, because both values
  are in `.env`, but a single typo still can't reach another company.
- **Commit SHAs cited in documents written before publication stop
  resolving.** The filter-repo commit map, kept in the private store,
  translates them.
- **Every future change** to Simpro or host facts goes in the private store
  first. Reviews include `scripts/check-public-safe.py`.
- **Public visibility is limited by GitHub's terms, not by the licence.**
  Under GitHub's terms, anyone may view and fork a public repository on
  GitHub; the licence governs only what they may do with the code.
