# ADR-018: Pin container images to release tags

- **Status:** **Accepted** — 2026-10-23 (Alex). Drafted by Claude at Alex's
  request (option 1 of the Open WebUI upgrade); proposed and accepted the same
  day. It supersedes the image tags named in ADR-001's Decision (`ollama/ollama`,
  `ghcr.io/open-webui/open-webui:main`); the rest of ADR-001 stands.
- **Date:** 2026-10-23
- **Deciders:** Alex
- **Related:** ADR-001 (local LLM stack); root `CLAUDE.md` §7 (exact-pinned
  dependencies); `docs/recovery-plan.md` §7 item 7 and §10;
  `scripts/backup.sh` (records running image digests).

## Context

ADR-001 names two images by floating tags:

- `ghcr.io/open-webui/open-webui:main`
- `ollama/ollama` (implicitly `latest`)

Its Consequences call this "a reproducibility trade-off worth revisiting". It
points at `docs/known-issues.md`, which has no such entry. The other images in
`docker-compose.yml` are already pinned: `pgvector/pgvector:0.8.6-pg16`,
`apache/tika:3.3.1.0-full` and `postgres:16-alpine`, the last to a major
version only.

What the floating tags cause, checked on 2026-10-23:

- **`main` is not a release.** It is rebuilt from Open WebUI's default branch
  between releases. The running container reports 0.11.0, but was built on
  2026-10-05, while 0.11.0 was released on 2026-07-27. Today `main`,
  `v0.12.3` and `dev` each point at a different image digest.
- **A `pull` upgrades without a decision.** Open WebUI 0.12.1 changes the
  database schema, and its release notes "strongly recommend" a backup
  first. After the migration, an older image cannot read `webui.db`, so a
  rollback means restoring from backup. With a floating tag, that can happen
  on any `docker compose pull` or rebuild, including during a restore
  (`docs/recovery-plan.md` §7 item 7 records this risk).
- **Audits name a version that cannot be named again.** The knowledge base
  audit (`docs/reviews/kb-audit-2026-10.md`) records "0.11.0", but that label
  does not identify the build that was tested.
- **Root `CLAUDE.md` §7 requires exact pins** for Python dependencies. The
  stack's own images have no equivalent rule.

Running versions on 2026-10-23: Open WebUI 0.11.0 (a `main` build), and
Ollama 0.31.2, whose image digest equals that of the `ollama/ollama:0.31.2`
tag. The latest Open WebUI release is v0.12.3 (2026-10-16).

## Decision

**Accepted: Option A** (Alex, 2026-10-23).

Every image in `docker-compose.yml` is referenced by an exact **release tag**:

| Service | From | To |
|---|---|---|
| `open-webui` | `ghcr.io/open-webui/open-webui:main` | `ghcr.io/open-webui/open-webui:v0.12.3` (the planned upgrade) |
| `ollama` | `ollama/ollama` | `ollama/ollama:0.31.2` (what runs today, so nothing changes) |

Upgrades become deliberate changes. Each one is a pull request that changes
the tag, made after:

1. reading the release notes between the two versions;
2. a verified `scripts/backup.sh` run;
3. keeping the old image under a local tag for rollback.

The PR records the result. `postgres:16-alpine` (major-version tag) is left
as it is: changing it is outside this upgrade, and the recovery plan already
records which image the backups use.

## Alternatives considered

| Option | What | For | Against |
|---|---|---|---|
| **A. Release tags (recommended)** | `image: …:v0.12.3` | Readable; matches the release notes read before an upgrade; one-line upgrades | A publisher could, rarely, re-push a tag; the digest the backup records still shows what ran |
| B. Tag plus digest | `image: …:v0.12.3@sha256:…` | Byte-for-byte reproducible | Every upgrade must also look up a digest; harder to read; the backup already records digests |
| C. Keep floating tags | Status quo, digests recorded by the backup | No work | Silent upgrades with schema migrations; audits cannot name a version |

## Consequences

- **Positive:** no `pull` changes a version unless a PR says so. A restore
  brings back the version that wrote the backup. The audit and the release
  notes refer to the same version.
- **Negative:** security fixes arrive only when someone upgrades. Release
  notes need checking periodically; that is a manual step, not automated.
- **ADR-001:** its Status line records that its image tags are superseded by
  ADR-018. Its Decision text stays unchanged.
- **Revisit if:** a second host or CI starts building the stack (consider
  Option B), or upgrades become frequent enough to automate the release-notes
  check.
