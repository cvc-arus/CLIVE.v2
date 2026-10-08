"""The ``columns`` projection, and the response helpers it needs.

Simpro's ``columns`` parameter narrows a response to the named fields. The
contract documents it on **every** path, collection and detail alike, with the
example ``columns=ID,Name`` and ``collectionFormat: csv``.

It selects **top-level keys only**, and a selected key yields its whole nested
block: Simpro's forum documents ``?columns=CustomFields`` returning the entire
custom-fields array. So the projection is a filter over the dict
``serializers.py`` already built, not a partial traversal of it.

Returning a projected body means returning a ``JSONResponse``, which bypasses
the route's ``response_model`` — the body no longer has the declared shape, so
validating it against the full schema would fail. Two consequences, both
deliberate:

* Pagination headers must be passed to the ``JSONResponse`` explicitly.
  Headers set on the injected ``Response`` are **discarded** when a handler
  returns a ``Response`` of its own.
* The unprojected path still returns a plain dict and keeps its
  ``response_model`` validation, which is what catches serializer typos. Only
  a caller who asked for a projection gives that up.
"""

from typing import Any

from fastapi import Response
from starlette.responses import JSONResponse

from simpro_mock.middleware import pagination_headers, set_pagination_headers

#: Always present in a projected response, even when not asked for. A row
#: without its id cannot be followed to the detail route, and Simpro's own
#: documented example (``columns=ID,Name``) leads with it.
#:
#: **Unverified against live Simpro.** If the real API omits ``ID`` when it is
#: not requested, this is a convenience the mock invents, and callers must not
#: come to depend on it (``services/simpro_mock/CLAUDE.md`` §1). Re-check on
#: first live access.
ALWAYS_INCLUDED = "ID"


def parse_columns(columns: str | None) -> list[str] | None:
    """Parse the csv ``columns`` parameter.

    Args:
        columns: The raw parameter value, or ``None`` when absent.

    Returns:
        The requested field names, or ``None`` when no projection was asked
        for. An empty or whitespace-only value also yields ``None``, so
        ``?columns=`` behaves as if it had been omitted rather than returning
        rows with only an ``ID``.
    """
    if not columns:
        return None
    names = [name.strip() for name in columns.split(",") if name.strip()]
    return names or None


def project(payload: dict[str, Any], columns: list[str] | None) -> dict[str, Any]:
    """Narrow one response dict to the requested columns.

    Unknown names are **ignored**, not rejected. A caller may legitimately ask
    for a field the contract documents but this mock does not serve, such as
    the ``Totals`` block that is out of ADR-013's fidelity scope; real Simpro
    would return it, so a 400 here would be wrong. Unlike an ignored *filter*,
    an absent column is visible in the response and cannot mislead.

    Args:
        payload: A dict from ``serializers.py``.
        columns: Requested field names, or ``None`` to pass the dict through.

    Returns:
        The payload, or a copy holding only the requested keys plus ``ID``.
    """
    if columns is None:
        return payload
    wanted = {ALWAYS_INCLUDED, *columns}
    return {key: value for key, value in payload.items() if key in wanted}


def collection_response(
    response: Response,
    rows: list[dict[str, Any]],
    total: int,
    total_pages: int,
    columns: str | None,
) -> Any:
    """Return a collection body, projected when ``columns`` was supplied.

    Args:
        response: The injected response, used to carry headers on the
            unprojected path.
        rows: Serializer output, one dict per record.
        total: ``Result-Total``.
        total_pages: ``Result-Pages``.
        columns: The raw ``columns`` parameter.

    Returns:
        The list of dicts, so the route's ``response_model`` validates it, or
        a ``JSONResponse`` carrying the projected rows and the same headers.
    """
    requested = parse_columns(columns)
    if requested is None:
        set_pagination_headers(response, total, len(rows), total_pages)
        return rows
    return JSONResponse(
        content=[project(row, requested) for row in rows],
        headers=pagination_headers(total, len(rows), total_pages),
    )


def detail_response(payload: dict[str, Any], columns: str | None) -> Any:
    """Return a detail body, projected when ``columns`` was supplied.

    Args:
        payload: Serializer output for one record.
        columns: The raw ``columns`` parameter.

    Returns:
        The dict, so the route's ``response_model`` validates it, or a
        ``JSONResponse`` carrying the projected dict.
    """
    requested = parse_columns(columns)
    if requested is None:
        return payload
    return JSONResponse(content=project(payload, requested))
