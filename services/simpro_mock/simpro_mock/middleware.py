import math

from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from simpro_mock.config import settings


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer tokens on API routes, exempting health and token endpoints."""

    EXEMPT_PATHS = {
        "/health",
        "/oauth2/token",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Bearer token"},
            )

        token = auth_header.removeprefix("Bearer ")
        if token != settings.mock_access_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid access token"},
            )

        return await call_next(request)


def paginate_query(query, page: int, page_size: int, limit: int | None = None):
    """Apply pagination to a SQLAlchemy query. Returns (items, total, total_pages).

    The query must already be ordered — see ``ordering.apply_ordering``. An
    unordered ``.offset().limit()`` has no defined row order in PostgreSQL, so
    page boundaries would not be stable.

    ``limit`` is the contract's own parameter, described only as "Set the limit
    of number of records in a request". It is read here as a narrowing of
    ``pageSize``: the effective page size becomes the smaller of the two, and
    ``Result-Pages`` is computed from it, so every header still describes the
    result set as actually paged. **The exact upstream semantics are
    unverified** — "in a request" could instead mean a cap on the whole result
    set across pages. Re-check on first live access
    (``services/simpro_mock/CLAUDE.md`` §3).

    Args:
        query: An ordered query to page over.
        page: 1-based page number.
        page_size: The requested page size.
        limit: The contract's ``limit``, or ``None`` when absent.

    Returns:
        ``(items, total, total_pages)``, where ``total`` is the full filtered
        count and is not reduced by ``limit``.
    """
    effective_page_size = page_size if limit is None else min(page_size, limit)
    total = query.count()
    total_pages = math.ceil(total / effective_page_size) if total > 0 else 1
    offset = (page - 1) * effective_page_size
    items = query.offset(offset).limit(effective_page_size).all()
    return items, total, total_pages


def pagination_headers(total: int, count: int, total_pages: int) -> dict[str, str]:
    """Render the Simpro pagination headers as a plain dict.

    The dict form exists because a projected response is returned as its own
    ``JSONResponse``, and headers set on the injected ``Response`` are
    discarded in that case, so they have to be passed in explicitly.
    """
    return {
        "Result-Total": str(total),
        "Result-Count": str(count),
        "Result-Pages": str(total_pages),
    }


def set_pagination_headers(
    response: Response, total: int, count: int, total_pages: int
):
    """Set Simpro-compatible pagination response headers."""
    response.headers.update(pagination_headers(total, count, total_pages))
