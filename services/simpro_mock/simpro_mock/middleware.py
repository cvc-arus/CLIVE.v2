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


def paginate_query(query, page: int, page_size: int):
    """Apply pagination to a SQLAlchemy query. Returns (items, total, total_pages)."""
    total = query.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
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
