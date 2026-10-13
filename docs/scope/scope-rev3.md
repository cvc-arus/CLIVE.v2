> Historical — superseded by docs/STATUS.md and docs/course-correction-plan.md (2026-10-12).

# CLIVE Enterprise AI Platform — Scope & Roadmap (Revision 3)

**Company:** CVC · **Industry:** CCTV and Security
**Date:** 2026-10-09
**Supersedes:** Revision 2 (`RevisedScope.txt`) and the original `Clive_Scope.txt`.

## What changed since Revision 2

1. **New requirement:** any authorised CVC user can ask questions about Simpro
   data in Open WebUI, with access restricted by role. Confirmed as useful by
   informal user research (October 2026).
2. **New phase 3B — Simpro Conversational Access**, inserted between Phase 3 and
   Phase 4. See `PDD-phase3b-simpro-conversational-access.md`.
3. **ADR-009 resolved (proposed):** `clive-gateway` is the single runtime access
   point to Simpro. Phase 4 consumes the gateway's API, not `simpro_client`
   directly. This reverses the "library-first, direct import" assumption for Phase 4.
4. **Phase 5 split:** a minimum security slice (Nginx, HTTPS, LAN-only firewall,
   Open WebUI hardening) is pulled forward into Phase 3B Sprint 2. The remainder
   of Phase 5 is unchanged.
5. **Phase 3 Sprint 6** ("Phase 4 readiness review") is folded into the Phase 3B
   exit criteria, because Phase 4 now depends on the gateway.

## 1. Status summary

| Phase | Name | Status |
|---|---|---|
| 1 | Local AI Platform | ✅ Complete |
| 2 | Production RAG | ✅ Complete |
| 3 | Simpro API Integration | 🔶 Sign-off pending (status to be confirmed against the codebase) |
| 3B | Simpro Conversational Access | 📝 Planned — PDD drafted |
| 4 | Document Generation | ⏳ Blocked on Phase 3B |
| 5 | Security & Reverse Proxy (remainder) | ⏳ Not started; minimum slice delivered in 3B |
| 6–9 | Sales Agent, Tender Agent, Customer Intelligence, Multi-Agent | ⏳ Not started |
| 10 | Monitoring & Disaster Recovery | ⏳ Not started |

## 2. Phase 3 — remaining work to sign-off

- Confirm the Sprint 4 typed client layer (models, endpoints, pagination, rate
  limiter, 401/429 resilience per ADR-010) against the codebase and test suite.
- Phase 3 Sprint 5: hardening and documentation refresh.
- Accept ADR-009.

## 3. Phase 3B — Simpro Conversational Access (new)

**Goal:** authorised users ask questions about Simpro data in Open WebUI and get
accurate, role-restricted answers.

**Approach:** a fixed catalogue of read-only queries exposed by `clive-gateway`
and called by an Open WebUI tool (ADR-015). Permissions are enforced in the
gateway using a shared Client Credentials service account and CLIVE-managed
roles (ADR-014, Option 1).

| Sprint | Goal | Weeks |
|---|---|---|
| 1 | Decisions and design (ADRs, permission matrix, query catalogue, model spike) | 1 |
| 2 | Minimum security slice | 2 |
| 3 | Gateway foundation (service, DB, policy, audit) | 3–4 |
| 4 | Query catalogue v1 | 5–6 |
| 5 | Open WebUI integration | 7 |
| 6 | Pilot, hardening, Phase 4 handover | 8–9 |

**Entry criteria:** Phase 3 signed off; ADR-009 accepted.

## 4. Phase 4 — Document Generation (updated entry criteria)

**Entry criteria:**
1. Phase 3B exit criteria met.
2. Gateway query catalogue covers Customers, Sites, Contacts, Jobs, Quotes,
   Assets, Employees.
3. A `docgen` service account and role exist in the gateway.

**Changed:** Phase 4 consumes Simpro data through `clive-gateway` (ADR-009), so
user-triggered document generation respects the same permissions and audit.

Scope otherwise unchanged: quotes, RAMS, contracts, equipment specifications,
tender responses and technical documentation, with the Phase 2 knowledge base
as a candidate source of boilerplate.

## 5. Phase 5 — Security & Reverse Proxy (updated)

Delivered early in Phase 3B: Nginx reverse proxy, HTTPS on the LAN, LAN-only
firewall rules, Open WebUI hardening.

Remaining: external access (if ever required), full authentication review,
SSH hardening, secrets review, and any further items in the original scope.

## 6. Phases 6–10

Unchanged in scope. All Simpro access from these phases goes through
`clive-gateway` under ADR-009, using service accounts where no human user is involved.

## 7. Engineering standards (additions)

- `simpro_client` is imported at runtime only by `clive-gateway` (ADR-009).
  Tests and developer tooling against the mock are the exceptions.
- `clive-gateway` runs a single uvicorn worker while the rate limiter is per-process.
- Access control is enforced server-side and deny-by-default; never via prompts.
- Simpro data is never written to the PGVector knowledge base.
- Only admins may create or edit Open WebUI tools.
- SQLAlchemy remains synchronous across services unless a dedicated ADR says otherwise.
