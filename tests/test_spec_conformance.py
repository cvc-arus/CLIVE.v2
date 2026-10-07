"""Validate every client model against Simpro's published OpenAPI spec.

``simpro_client``'s models were built against ``simpro_mock``, whose payloads
were invented. This module is the oracle for re-shaping both to the vendor's
own contract: it generates payloads from
``docs/contracts/simpro-openapi-v1-get-subset.json`` and feeds them to the
models, so the question "would this code work against real Simpro?" has an
answer that does not need API access.

Two payload shapes per endpoint:

``full``
    Every documented property, populated. Catches wrong names, wrong types
    and wrong nesting.
``minimal``
    Only the properties the spec marks required, with nullable ones set to
    ``None``. This is the strict leg: it proves we never require a field
    Simpro may omit, and never reject a documented ``null``.

Known-nonconforming combinations live in ``spec_conformance_baseline.json``
rather than behind ``xfail`` markers, which ``tests/CLAUDE.md`` §7 rules out.
The baseline is data, and the test enforces it in both directions: a
combination outside the file must conform, and a combination inside it that
starts conforming fails until its entry is deleted. So the file can only
shrink, and progress is a deletion visible in ``git log -p``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from simpro_client.models import (
    Asset,
    Attachment,
    Company,
    Contact,
    Customer,
    Employee,
    Job,
    JobNote,
    ProjectStatusCode,
    Quote,
    Site,
)

API_PREFIX = "/api/v1.0"
CONTRACT_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "contracts"
    / "simpro-openapi-v1-get-subset.json"
)
BASELINE_PATH = Path(__file__).resolve().parent / "spec_conformance_baseline.json"

#: The baseline may never grow. Lower this literal as entries are deleted;
#: raising it means the re-shape went backwards.
MAX_BASELINE_ENTRIES = 40

#: ``(name, model, list path, detail path)`` for every resource the client
#: reads. ``Project`` is absent on purpose: Simpro has no Projects resource,
#: so there is nothing to conform to. See ADR-013.
RESOURCES: tuple[tuple[str, type[BaseModel], str, str], ...] = (
    ("Company", Company, "/companies/", "/companies/{companyID}"),
    (
        "Customer",
        Customer,
        "/companies/{companyID}/customers/",
        "/companies/{companyID}/customers/individuals/{customerID}",
    ),
    ("Job", Job, "/companies/{companyID}/jobs/", "/companies/{companyID}/jobs/{jobID}"),
    (
        "Quote",
        Quote,
        "/companies/{companyID}/quotes/",
        "/companies/{companyID}/quotes/{quoteID}",
    ),
    (
        "Contact",
        Contact,
        "/companies/{companyID}/customers/{customerID}/contacts/",
        "/companies/{companyID}/customers/{customerID}/contacts/{contactID}",
    ),
    (
        "Site",
        Site,
        "/companies/{companyID}/sites/",
        "/companies/{companyID}/sites/{siteID}",
    ),
    (
        "Asset",
        Asset,
        "/companies/{companyID}/sites/{siteID}/assets/",
        "/companies/{companyID}/sites/{siteID}/assets/{assetID}",
    ),
    (
        "Employee",
        Employee,
        "/companies/{companyID}/employees/",
        "/companies/{companyID}/employees/{employeeID}",
    ),
    (
        "JobNote",
        JobNote,
        "/companies/{companyID}/jobs/{jobID}/notes/",
        "/companies/{companyID}/jobs/{jobID}/notes/{noteID}",
    ),
    (
        "Attachment",
        Attachment,
        "/companies/{companyID}/jobs/{jobID}/attachments/files/",
        "/companies/{companyID}/jobs/{jobID}/attachments/files/{fileID}",
    ),
    (
        "ProjectStatusCode",
        ProjectStatusCode,
        "/companies/{companyID}/setup/statusCodes/projects/",
        "/companies/{companyID}/setup/statusCodes/projects/{statusCodeID}",
    ),
)

_TYPE_DEFAULTS: dict[str, Any] = {
    "integer": 1,
    "number": 1.57,
    "boolean": True,
    "string": "x",
}


@lru_cache(maxsize=1)
def _contract() -> dict[str, Any]:
    """Return the vendored OpenAPI subset, parsed once per session."""
    return json.loads(CONTRACT_PATH.read_text())


@lru_cache(maxsize=1)
def _baseline() -> dict[str, Any]:
    """Return the known-nonconforming combinations, parsed once per session."""
    return json.loads(BASELINE_PATH.read_text())


def _is_nullable(schema: dict[str, Any]) -> bool:
    """Report whether the spec allows ``null`` for this schema."""
    return bool(schema.get("nullable") or schema.get("x-nullable"))


def _sample(schema: dict[str, Any], *, minimal: bool) -> Any:
    """Build a spec-conformant value for ``schema``.

    Args:
        schema: An OpenAPI 2.0 schema node.
        minimal: When true, emit only required properties and use ``None``
            for anything the spec marks nullable.

    Returns:
        A value the spec permits for this schema.
    """
    if minimal and _is_nullable(schema):
        return None

    kind = schema.get("type")
    if kind == "object":
        required = set(schema.get("required", ()))
        return {
            name: _sample(subschema, minimal=minimal)
            for name, subschema in schema.get("properties", {}).items()
            if not minimal or name in required
        }
    if kind == "array":
        items = schema.get("items", {"type": "string"})
        return [_sample(items, minimal=minimal)]
    if "example" in schema:
        return schema["example"]
    return _TYPE_DEFAULTS.get(kind)


def _response_schema(path: str) -> dict[str, Any]:
    """Return the 200 response schema for a path's GET, unwrapping arrays.

    The real API returns a bare JSON array from collection routes, with no
    envelope object, so unwrapping ``items`` here is what lets the list leg
    assert that shape.
    """
    operation = _contract()["paths"][API_PREFIX + path]["get"]
    schema = operation["responses"]["200"]["schema"]
    return schema.get("items", schema)


def _cases() -> list[tuple[str, type[BaseModel], str, str, bool]]:
    """Enumerate ``(name, model, kind, path, minimal)`` for every check."""
    cases = []
    for name, model, list_path, detail_path in RESOURCES:
        for kind, path in (("list", list_path), ("detail", detail_path)):
            for minimal in (False, True):
                cases.append((name, model, kind, path, minimal))
    return cases


CASES = _cases()


def _case_id(case: tuple[str, type[BaseModel], str, str, bool]) -> str:
    """Render a case as the dotted key used by the baseline file."""
    name, _model, kind, _path, minimal = case
    return f"{name}.{kind}.{'minimal' if minimal else 'full'}"


@pytest.mark.parametrize("case", CASES, ids=_case_id)
def test_model_matches_published_spec(
    case: tuple[str, type[BaseModel], str, str, bool],
) -> None:
    """Each model validates a payload generated from the published spec.

    A combination listed in ``spec_conformance_baseline.json`` is expected to
    fail; when it stops failing, this test fails so the entry gets deleted.
    """
    name, model, kind, path, minimal = case
    key = _case_id(case)
    payload = _sample(_response_schema(path), minimal=minimal)

    # Collection routes return a bare array, so validate the array shape too.
    adapter: TypeAdapter[Any] = TypeAdapter(
        list[model] if kind == "list" else model  # type: ignore[valid-type]
    )
    body = [payload] if kind == "list" else payload

    error: str | None = None
    try:
        adapter.validate_python(body)
    except ValidationError as exc:
        error = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}:{item['type']}"
            for item in exc.errors()
        )

    entry = _baseline().get(key)
    if entry is None:
        assert error is None, (
            f"{key} does not match {CONTRACT_PATH.name}: {error}. "
            f"Either fix {model.__name__} or add {key} to {BASELINE_PATH.name} "
            f"with a reason."
        )
    else:
        assert error is not None, (
            f"{key} now conforms. Delete its entry from {BASELINE_PATH.name} "
            f"(recorded reason: {entry.get('reason', 'none given')})."
        )


def test_baseline_entries_all_name_a_real_case() -> None:
    """No stale keys: every baseline entry names a case this module checks."""
    known = {_case_id(case) for case in CASES}
    unknown = sorted(set(_baseline()) - known)
    assert not unknown, (
        f"{BASELINE_PATH.name} names combinations that no longer exist: "
        f"{unknown}. Delete them."
    )


def test_baseline_never_grows() -> None:
    """The baseline may only shrink, so the re-shape cannot regress."""
    count = len(_baseline())
    assert count <= MAX_BASELINE_ENTRIES, (
        f"{BASELINE_PATH.name} has {count} entries but "
        f"MAX_BASELINE_ENTRIES is {MAX_BASELINE_ENTRIES}. Adding "
        f"nonconforming combinations is a regression."
    )


def test_every_baseline_entry_documents_itself() -> None:
    """Each entry carries a reason and the sprint that will remove it."""
    incomplete = sorted(
        key
        for key, entry in _baseline().items()
        if not entry.get("reason") or not entry.get("fixed_by")
    )
    assert not incomplete, (
        f"{BASELINE_PATH.name} entries missing 'reason' or 'fixed_by': {incomplete}"
    )
