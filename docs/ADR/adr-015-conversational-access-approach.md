# ADR-015: Conversational access approach for Simpro data

- **Status:** Proposed
- **Date:** 2026-10-09; revised 2026-11-03 (Claude, at Alex's request):
  options D–H added, context updated for live Simpro access and ADR-014's
  acceptance. The proposed decision is unchanged
- **Deciders:** Alex
- **Related:** ADR-009 (`clive-gateway` as the single Simpro access point),
  ADR-010 (rate limiting), ADR-014 (access control model, accepted
  2026-11-03), ADR-017 (private build facts). Candidate catalogue: Phase 3B
  PDD §8 (`docs/PDDs/PDD-phase3b-simpro-conversational-access.md`)

## Context

Users will ask natural-language questions about Simpro data in Open WebUI and
expect answers from live data. The local LLM (Ollama, RTX 3080 10 GB) needs a
way to obtain the data required to answer accurately, while respecting
ADR-014 access control.

Constraints that bound the options:

- **Access control lives in `clive-gateway`** (ADR-014, accepted 2026-11-03):
  server-side, deny by default, never via prompts. Only the two configured
  companies are ever queried, and every user may see both.
- **The gateway is the only read boundary.** CVC's API application has no
  dedicated read-only Simpro security group
  (`docs/simpro/simpro-api-findings.md` §2.2), so ADR-014 requires the gateway
  to expose only a fixed query catalogue and never pass raw paths or
  arbitrary company IDs through to Simpro.
- **Live Simpro is read-only** (root `CLAUDE.md` §3). Live access arrived
  2026-10-16 via OAuth2 Client Credentials, one service identity.
- **Self-hosted.** No cloud AI providers or external SaaS calls without
  Alex's explicit approval; CVC's Simpro build is the one approved external
  API.
- **Throughput.** Simpro documents 10 requests per second per build;
  `simpro_client` limits itself to 8 per client instance (ADR-010), and a new
  token invalidates the old one, so only one client should hold the
  credentials at a time.
- **API shape.** Collection routes return minimal fields unless `columns` is
  sent, and the mock cannot filter jobs or quotes by customer, site or staff
  member. Whether live Simpro can is unverified (see the live checks in
  Consequences).
- **Open WebUI 0.12.3** (ADR-018) runs tools in Native function-calling mode,
  the only supported mode since v0.10.0, and passes the signed-in user to
  Workspace tools as `__user__` (Open WebUI documentation, Tools).

## Options considered

A–C are unchanged from the 2026-10-09 text. D–H were added on 2026-11-03. E
is a delivery choice that can combine with A or D, not an alternative data
approach.

### Option A — Tool calling over a fixed query catalogue
An Open WebUI tool calls `clive-gateway` endpoints, each a read-only,
parameterised query. The model selects the query and arguments; Python computes
the results.
- Pro: live data; permissions enforced per query; each query testable.
- Pro: arithmetic and aggregation done in code, not by the model.
- Pro: typed, enum-heavy arguments suit small local models.
- Con: only catalogue questions can be answered; the catalogue grows over time.
- Con: questions needing many records (rankings, trends) exceed any per-query
  request budget.

### Option B — Text-to-SQL over a synced copy
The model writes SQL against a replicated Simpro dataset.
- Pro: flexible, in theory.
- Con: small local models produce plausible but wrong SQL.
- Con: needs a sync/caching layer (previously out of scope).
- Con: row and field restrictions are hard to guarantee over arbitrary SQL.
- Con: built against the mock schema, which is not guaranteed to match real Simpro.

### Option C — Embed Simpro records in the PGVector knowledge base
- Pro: easiest to wire up.
- Con: stale immediately; RAG cannot count, total or filter reliably.
- Con: no per-user filtering in the knowledge base, so it bypasses ADR-014 entirely.

### Option D — Resource tools with allow-listed filters
One tool per resource (`query_jobs`, `query_quotes`, …) instead of one per
question. The model passes filters, sort and a period; the gateway accepts
only the fields and operators allow-listed for that resource and builds the
Simpro request itself.
- Pro: live data; covers more questions with fewer tools.
- Pro: stays within ADR-014 as long as no raw path, raw filter string or
  `columns` list reaches Simpro.
- Con: the model composes filters, where small models make argument errors.
- Con: harder to test exhaustively than named queries; every filter
  combination is a code path.
- Con: inherits Simpro's filter gaps exactly as A does.

### Option E — Deliver the tools through an MCP or OpenAPI tool server
Open WebUI connects to MCP servers over HTTP and can turn an OpenAPI spec into
tools (Open WebUI documentation, Tools). The gateway, or a thin adapter, would
be registered directly instead of through a Python Workspace tool.
- Pro: no tool code inside Open WebUI; other clients could reuse the same
  tools later.
- Pro: the gateway's FastAPI OpenAPI schema already is the published contract
  (Phase 3B PDD §9).
- Con: a Workspace tool receives the signed-in user as `__user__`; an
  external tool server needs a verified way to receive the user's identity,
  or ADR-014's per-user rules cannot work.
- Con: whatever holds the gateway's service secret must be admin-only, as for
  a Workspace tool (PDD §10).

### Option F — Per-user Simpro login (Authorization Code)
Each user signs in to Simpro and queries run with their own token, as
community MCP servers for Simpro already do (`ozmarks/simpro-mcp` on GitHub).
- Pro: live data; Simpro is the source of truth for permissions.
- Con: this is ADR-014's Option 2, deferred there: per-user refresh tokens
  break the "tokens in memory only" rule, and how Simpro applies permissions
  under this grant is unverified.
- Con: needs a registered redirect URI reachable from the browser; the
  community server's multi-user mode needs a public web address, against the
  LAN-only design.

### Option G — Local replica kept fresh by webhooks or polling, queried by fixed queries
A CLIVE-owned copy of selected resources, refreshed from Simpro, with
catalogue queries running against it rather than against the API. Not
text-to-SQL: the queries stay fixed and ADR-014 is still enforced in the
gateway.
- Pro: rankings, trends and cross-record questions become cheap.
- Pro: no per-question load on Simpro's 10 req/s build limit.
- Con: near-real-time at best. Simpro's webhooks cover only job and quote
  created/updated events, so everything else needs polling.
- Con: webhooks need Simpro (cloud) to reach a CLIVE endpoint, which
  conflicts with the LAN-only design (`docs/simpro/simpro-api-findings.md` §2.6).
- Con: a sync layer, its own database and backups, and a second copy of
  client data to secure.

### Option H — Third-party Simpro sync service with its own MCP server
Commercial services sync Simpro into a managed warehouse and expose it to AI
assistants through MCP. Examples are Tugger, which advertises from £125 a
month and works with Claude, ChatGPT or Gemini, and SyncHub, which can also
sync to Postgres (vendor websites, checked 2026-11-03).
- Pro: fastest route; aggregations and cross-system questions out of the box.
- Con: CVC's client data leaves CVC's control, and the assistants are usually
  cloud models; both conflict with the self-hosted rule.
- Con: access control sits in the vendor's product, outside ADR-014.
- Con: freshness depends on the vendor's sync interval; recurring cost.

### Comparison

Only A and D give live data, stay inside ADR-014 and suit a 10 GB local
model; G is the candidate for what they cannot answer.

| Option | Data freshness | Fits ADR-014 | Fits self-hosted rule | Local model fit | Main cost |
|---|---|---|---|---|---|
| A Fixed catalogue | Live | Yes | Yes | Best: named queries, typed arguments | Limited question coverage |
| D Resource tools | Live | Yes, with allow-lists | Yes | Moderate: model composes filters | Argument errors; larger test surface |
| E MCP / OpenAPI delivery | As A or D | Only if user identity is forwarded | Yes | As A or D | Identity plumbing |
| F Per-user login | Live | Replaces it (ADR-014 Option 2) | Needs a reachable redirect | As A | Deferred in ADR-014 |
| G Replica + fixed queries | Near-live | Yes | Yes, if webhooks avoided | Good | Sync layer; inbound webhooks or polling |
| H Third-party SaaS | Vendor sync interval | No | No | Usually cloud models | Data leaves CVC; subscription |
| B Text-to-SQL | Sync interval | No | Yes | Poor | Wrong SQL; unenforceable restrictions |
| C Knowledge base | Stale | No | Yes | Poor | Bypasses ADR-014 |

## Decision

**Proposed: Option A.** Options B, C, F and H are rejected; D and E are open
until Phase 3B Sprint 1; G is deferred. Simpro data must never be written to
the PGVector knowledge base. Nothing here is a decision until Alex accepts it.

- **A** is the proposed approach, starting from the candidate catalogue in
  Phase 3B PDD §8.
- **D** is compared with A in the Sprint 1 model spike, on the same
  questions. If D's tool-choice and argument accuracy is close to A's, a
  hybrid (named queries for common questions, one allow-listed resource tool
  per resource for the rest) may be proposed in a revision of this ADR.
- **E** is an open delivery choice. The Phase 3B PDD's Workspace tool stays
  the default. An MCP or OpenAPI tool server may replace it only if Open WebUI
  can pass the signed-in user's identity to it in a way the gateway can verify.
- **F** stays deferred with ADR-014 Option 2 and is revisited under that
  ADR's triggers, not this one.
- **G** is deferred to the caching ADR the Phase 3B PDD plans for Sprint 6,
  if the pilot shows questions A cannot answer within its request budgets. A
  polling-only replica avoids the inbound webhook conflict.
- **H** is rejected: it sends CVC's client data outside CVC and puts access
  control outside ADR-014. Revisiting it needs Alex's explicit approval under
  the self-hosted rule.

## Consequences

- Sprint 1 of Phase 3B must produce a query catalogue from real user
  questions. The PDD §8 list is a candidate list until those questions are
  mapped to it.
- Before acceptance, read-only live checks must establish whether Simpro can
  filter jobs and quotes by customer and site, by staff member, and by
  partial text match. If Simpro cannot filter by related records, A answers
  those questions only for recent records, and G moves from deferred to
  needed. The checks follow root `CLAUDE.md` §3 and §9 (GETs only; counts
  and pass/fail only).
- Unsupported questions are logged during the pilot to drive catalogue v2,
  through a `report_unsupported` tool that writes an audit row and makes no
  Simpro call.
- The chosen model must handle tool calls reliably; a model evaluation is
  part of Sprint 1, and it tests A and D on the same questions.
- Query results are capped and summarised before reaching the model. Each
  query has a request budget so one question cannot exhaust Simpro's
  per-build rate limit.
- Free text from Simpro (notes, descriptions, custom fields) reaching the
  model is treated as data, length-capped, and returned only by queries that
  need it.
- The gateway's API is shaped so either Workspace-tool or tool-server
  delivery (E) can use it without change.

## Revisit if

- Users consistently need questions the catalogue cannot reasonably cover
  (consider D, or G under a caching ADR).
- Live checks show Simpro cannot filter jobs and quotes by customer, site or
  staff member (G becomes needed).
- The Sprint 1 spike shows D's accuracy matches A's on the evaluation set.
- Open WebUI gains a verifiable way to pass user identity to MCP or OpenAPI
  tool servers (E).
- ADR-014 is revisited for per-user Simpro login (F).
- A hardware upgrade makes much larger models practical.

## Revision notes (2026-11-03)

- Added Options D–H, the comparison table, and dispositions for each.
- Context updated for live access (2026-10-16), no dedicated Simpro security
  group, ADR-014's acceptance, Open WebUI 0.12.3 and Native tool calling.
- Consequences: live checks before acceptance, `report_unsupported`, request
  budgets, free-text handling.
- Proposed decision (Option A) and the rejections of B and C unchanged.
  Status stays Proposed.
