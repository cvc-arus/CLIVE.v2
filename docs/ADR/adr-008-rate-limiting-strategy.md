# ADR-008: Client-Side Rate Limiting — Token Bucket at 8 req/sec

## Status
**Proposed — not yet implemented.** No `rate_limiter.py` exists in `src/simpro_client/` at time of writing. This ADR records the original design intent from the Phase 3 PDD so the decision isn't lost, and flags it as outstanding work.

## Context
Real Simpro documents a shared rate limit of 10 requests/second **per build**, shared across every application connected to that build — not just `simpro_client`. Exceeding it risks throttling every other integration on the same Simpro build, not just CLIVE's own traffic. Simpro's `Retry-After` header behavior on `429` is not documented, so blind retries could worsen throttling rather than resolve it.

## Decision (as originally proposed, still pending implementation)
Implement a **token-bucket rate limiter** in `simpro_client`, budgeting **8 requests/second** — deliberately below the documented 10/sec ceiling to leave headroom for other applications on the same build — combined with exponential backoff with jitter on any `429` response, regardless of whether `Retry-After` is present.

`SimproRateLimitError` (in `exceptions.py`) already carries an optional `retry_after` field, so the exception type is ready for a rate limiter to consume — but nothing currently raises it from a client-enforced limit; today it can only originate from a `429` response the *server* returns, and `simpro_mock` deliberately never returns `429` (see the ADR on mocking Simpro), so this path has never actually been exercised even in testing.

## Alternatives Considered
- **No client-side limiting, rely entirely on server-side `429` + retry** — risk: since the limit is shared across all of CVC's Simpro-connected applications, waiting to be throttled reactively could degrade other integrations before `simpro_client` even notices.
- **A fixed sleep between requests** instead of a token bucket — simpler, but wastes throughput during bursts of infrequent calls and doesn't smooth out genuinely bursty workloads as well.

## Consequences If Implemented As Proposed
- Positive: protects shared Simpro rate-limit budget proactively rather than reactively.
- Positive: `SimproRateLimitError.retry_after` is already wired for a limiter to raise/consume.
- Risk: cannot be validated against real Simpro behavior until live API access is enabled, since the mock never emits `429`. Testing this properly will require either a live sandbox or deliberately extending `simpro_mock` to simulate rate limiting (currently explicitly out of scope for the mock).

## Recommendation
Build this as part of the Phase 3 typed-client-layer work (alongside `pagination.py`), before Phase 3 sign-off, since it's a documented risk in the original PDD that hasn't yet been mitigated in code.
