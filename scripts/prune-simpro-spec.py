#!/usr/bin/env python
"""Prune Simpro's full OpenAPI 2.0 spec to the GET operations CLIVE consumes.

Simpro publishes a single ~27 MB ``swagger.json`` covering 719 paths. Phase 3
reads twelve resources and issues only GET, so committing the whole file would
add tens of megabytes of irrelevant write and setup operations to the
repository. This script extracts just the paths in ``KEEP_PATHS``, keeps only
their ``get`` operations, and writes a self-contained subset of roughly 250 KB.

The subset is the normative contract for ``simpro_client``'s field names,
types and required/optional status. Re-run this script whenever Simpro
publishes a new spec, then re-run ``tests/test_spec_conformance.py`` to see
what changed.

The relevant operations contain no ``$ref``, so the subset needs no
``definitions`` section and can be read without resolution.

Usage:
    uv run python scripts/prune-simpro-spec.py <full-spec.json> <output.json>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

API_PREFIX = "/api/v1.0"

#: Paths CLIVE reads, without the ``/api/v1.0`` prefix. Ordered by resource so
#: the diff of a regenerated subset stays readable.
KEEP_PATHS: tuple[str, ...] = (
    "/companies/",
    "/companies/{companyID}",
    "/companies/{companyID}/customers/",
    "/companies/{companyID}/customers/individuals/",
    "/companies/{companyID}/customers/individuals/{customerID}",
    "/companies/{companyID}/customers/companies/",
    "/companies/{companyID}/customers/companies/{customerID}",
    "/companies/{companyID}/customers/{customerID}/contacts/",
    "/companies/{companyID}/customers/{customerID}/contacts/{contactID}",
    "/companies/{companyID}/jobs/",
    "/companies/{companyID}/jobs/{jobID}",
    "/companies/{companyID}/jobs/{jobID}/notes/",
    "/companies/{companyID}/jobs/{jobID}/notes/{noteID}",
    "/companies/{companyID}/jobs/{jobID}/attachments/files/",
    "/companies/{companyID}/jobs/{jobID}/attachments/files/{fileID}",
    "/companies/{companyID}/quotes/",
    "/companies/{companyID}/quotes/{quoteID}",
    "/companies/{companyID}/sites/",
    "/companies/{companyID}/sites/{siteID}",
    "/companies/{companyID}/sites/{siteID}/assets/",
    "/companies/{companyID}/sites/{siteID}/assets/{assetID}",
    "/companies/{companyID}/employees/",
    "/companies/{companyID}/employees/{employeeID}",
    "/companies/{companyID}/setup/statusCodes/projects/",
    "/companies/{companyID}/setup/statusCodes/projects/{statusCodeID}",
)

#: Top-level keys carried over from the source spec.
PRESERVED_KEYS: tuple[str, ...] = (
    "swagger",
    "info",
    "basePath",
    "schemes",
    "consumes",
    "produces",
)


def prune(spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a GET-only subset of ``spec`` plus any missing paths.

    Args:
        spec: The full parsed OpenAPI 2.0 document.

    Returns:
        A ``(subset, missing)`` pair. ``missing`` names any entry of
        ``KEEP_PATHS`` absent from the source spec, or present without a
        ``get`` operation, so a vendor removal is reported rather than
        silently dropped.
    """
    subset: dict[str, Any] = {k: spec[k] for k in PRESERVED_KEYS if k in spec}
    paths: dict[str, Any] = {}
    missing: list[str] = []

    for path in KEEP_PATHS:
        full = API_PREFIX + path
        operations = spec.get("paths", {}).get(full)
        if operations is None or "get" not in operations:
            missing.append(path)
            continue
        paths[full] = {"get": operations["get"]}

    subset["paths"] = paths
    return subset, missing


def main(argv: list[str]) -> int:
    """Write the pruned subset and report what it contains."""
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2

    source, destination = Path(argv[1]), Path(argv[2])
    spec = json.loads(source.read_text())
    subset, missing = prune(spec)

    for path in missing:
        print(f"WARNING: not in source spec, omitted: {path}", file=sys.stderr)

    payload = json.dumps(subset, indent=1, sort_keys=True) + "\n"
    destination.write_text(payload)

    print(
        f"{source.name}: {len(spec.get('paths', {}))} paths "
        f"-> {destination.name}: {len(subset['paths'])} GET paths, "
        f"{len(payload) / 1024:.0f} KB"
    )
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
