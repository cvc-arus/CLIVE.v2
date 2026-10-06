# ADR-011: Exception Hierarchy and Authentication Error Context

*   **Status:** Accepted (2026-10-06, ARus)
*   **Deciders:** ARus
*   **Date:** 2026-10-06 UTC
*   **Context/Phase:** Phase 3, `simpro_client`
*   **Relates to:** ADR-005 (auth strategy), ADR-010 (resilience policy).
    Supersedes ADR-010 §2.5 only.

---

## 1. Context

ADR-010 §2.5 sets out the client's exception hierarchy. It does not match the
exceptions the client actually raises:

- It leaves out `SimproAuthError`, which has existed since Sprint 1
  (ADR-005) and is raised whenever a token cannot be obtained.
- It leaves out `SimproNotFoundError` (404) and the `SimproAPIError` layer
  between `SimproError` and the 4xx/5xx classes. That layer is kept for
  backward compatibility and is already recorded as a deviation in
  `src/simpro_client/CLAUDE.md`.
- ADR-010 §2.2 says a failed refresh after a 401 raises `SimproClientError`.
  `SimproAuthRefreshError(SimproClientError, SimproAuthError)` was added on
  2026-10-06 to satisfy this without breaking callers that catch
  `SimproAuthError`, but §2.5 doesn't list it.

ADR-010 §2.4 also requires every final raised exception to expose the
request's correlation ID. Before this change, `SimproAuthError` carried only a
message. When the first token fetch failed during a request, the caller got no
correlation ID, method, URL or token-endpoint status.

docs/CLAUDE.md §4 says an Accepted/Approved ADR's Decision must not be edited,
so the correction is recorded here.

## 2. Decision

### 2.1 Exception hierarchy (replaces ADR-010 §2.5)

```
SimproError
├── SimproAuthError              token could not be obtained
│                                (status_code, method, url, correlation_id)
├── SimproProtocolError          bad or missing pagination headers
└── SimproAPIError               (status_code, response_body, method, url,
    │                             correlation_id, retry_count)
    ├── SimproClientError        4xx
    │   ├── SimproNotFoundError  404
    │   ├── SimproRateLimitError 429 (retry_after, attempt_count)
    │   └── SimproAuthRefreshError
    │                            401: the refresh after a 401 failed;
    │                            also a SimproAuthError
    └── SimproServerError        5xx
```

### 2.2 `SimproAuthError` context

`SimproAuthError(message, *, status_code=None, method=None, url=None,
correlation_id=None)`. All context fields are keyword-only and optional, so
existing `SimproAuthError("...")` calls still work.

- `status_code` is the **token endpoint's** HTTP status. It is `None` when no
  response was received (transport error) or no request was made (API-key
  mode with no key).
- `method`, `url` and `correlation_id` describe the **API request** that
  needed the token. `SimproClient._request_response()` fills them in when a
  token fetch fails, which meets ADR-010 §2.4.
- When the refresh after a 401 fails, `SimproAuthRefreshError` is raised
  instead (ADR-010 §2.2). Its `status_code` is the API's 401. The original
  `SimproAuthError`, with the token endpoint's status, is its `__cause__`.

### 2.3 Initialisation order

`SimproAPIError.__init__` calls `super().__init__()` **before** setting its
own attributes. Otherwise, in `SimproAuthRefreshError`'s method resolution
order, `SimproAuthError.__init__` would reset the API context to `None`.

## 3. Alternatives considered

1. **Make `SimproAuthError` a subclass of `SimproClientError`.** Rejected.
   It would force a 4xx `status_code` and API context onto configuration
   errors and token-endpoint timeouts, which have neither. It also changes the
   hierarchy for every caller.
2. **Keep `SimproAuthError` message-only and record the missing correlation
   ID as a deviation.** Rejected. Auth failures are the hardest to trace
   without the correlation ID, and ADR-010 §2.4 explicitly requires it.
3. **Leave ADR-010 §2.5 as written.** Rejected. The record would stay wrong
   about which exceptions callers can catch.

## 4. Consequences

*   **Positive:** The documented hierarchy matches `exceptions.py`. Every
    exception raised during a request now carries its correlation ID.
*   **Positive:** The change only adds fields. Existing `except` clauses and
    constructor calls keep working.
*   **Negative:** `status_code` means different things on the two auth
    classes: the token endpoint's status on `SimproAuthError`, the API's 401 on
    `SimproAuthRefreshError`. This is documented on both classes.
*   **Negative:** `SimproAuthRefreshError` uses multiple inheritance, which
    relies on the initialisation order in §2.3. This is covered by
    `tests/test_retries.py`.

## 5. Follow-up on acceptance (done 2026-10-06)

- `docs/ADR/adr-010-resilience-policy.md`: Status line only, noting that
  §2.5 is superseded by ADR-011.
- `docs/ADR/ADR-index.md`, `docs/README.md` §5 and root `CLAUDE.md` §4:
  status changed from Proposed to Accepted.

## 6. Verification

- `tests/test_auth.py`: the token endpoint's status is set on rejection, and
  is `None` on a transport error.
- `tests/test_retries.py`: a failed first token fetch through the client
  carries `method`, `url`, `correlation_id` and the token status. A failed
  refresh after a 401 raises `SimproAuthRefreshError` with the API context,
  and the cause's token status is set.
- `uv run pytest -q -m "not integration"`.
