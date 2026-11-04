"""Opt-in, read-only data-quality audit of CVC's live Simpro (course correction W7).

Skipped unless **both** ``SIMPRO_LIVE_TESTS=1`` and ``SIMPRO_DATA_AUDIT=1``
are set, so the ordinary live contract run never starts this scan (about
6,700 GET requests, roughly 15 minutes at the client's rate limit).

The rules are those of ``tests/test_live_contract.py``, whose settings check
and guarded client this module reuses:

* **GET only**, and only routes of the two configured companies; the request
  hook fails anything else before it is sent.
* **No client data in output** (root ``CLAUDE.md`` §9). Every failure message
  is written here and holds a check ID, a count, a field name or an exception
  *type*, never a value or an exception message. Run with ``--tb=no``.
* **Findings go only to the private report**, under
  ``docs/simpro/private/data-audit/<date>/``. The writer refuses to write
  unless git ignores that directory. Claude Code never reads the report.

Run only when Alex asks::

    COLUMNS=200 SIMPRO_LIVE_TESTS=1 SIMPRO_DATA_AUDIT=1 uv run pytest \\
        tests/test_live_data_quality.py -m live -v --tb=no -rfE

``COLUMNS=200`` keeps pytest from cutting the counts off the short summary.

The check logic and its edge cases are in ``tests/simpro_data_checks.py``
and are tested offline in ``tests/test_simpro_data_checks.py``.
"""

import logging
import os
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import pytest

from simpro_client.client import SimproClient
from simpro_client.config import SimproSettings
from tests import simpro_data_checks as dq
from tests.test_live_contract import (  # noqa: F401 (live_settings is a fixture)
    live_settings,
    open_client,
)

pytestmark = pytest.mark.live

#: The private, git-ignored report root (ADR-017).
AUDIT_ROOT = Path(__file__).resolve().parents[1] / "docs/simpro/private/data-audit"

PAGE_SIZE = 250

#: ``columns`` per collection. Only what the checks use: no notes, custom
#: fields or amounts, so they cannot reach the report.
SITE_COLUMNS = ["ID", "Name", "Address", "Customers", "PrimaryContact", "Archived"]
COMPANY_CUSTOMER_COLUMNS = [
    "ID",
    "CompanyName",
    "Email",
    "Phone",
    "AltPhone",
    "Sites",
    "Contacts",
    "Archived",
]
INDIVIDUAL_CUSTOMER_COLUMNS = [
    "ID",
    "GivenName",
    "FamilyName",
    "Email",
    "Phone",
    "AltPhone",
    "CellPhone",
    "Sites",
    "Contacts",
    "Archived",
]
JOB_COLUMNS = ["ID", "Stage", "Site", "Customer"]
QUOTE_COLUMNS = ["ID", "Stage", "IsClosed", "Site", "Customer"]
ASSET_COLUMNS = ["ID", "ParentID", "Archived"]


@dataclass
class Fetched:
    """One collection's rows plus what the summary needs about the fetch."""

    rows: list[dict[str, Any]]
    total_at_start: int
    dropped: int
    absent: dict[str, int]


def fetch_all(client: SimproClient, path: str, columns: Sequence[str]) -> Fetched:
    """Fetch every page of a collection as raw rows, de-duplicated by ID.

    Pages are counted from the first response's ``Result-Pages``; the loop
    also stops early on an empty page, so a shrinking collection cannot spin.
    Raises :class:`~tests.simpro_data_checks.ProjectionError` if a requested
    column is absent from every row.
    """
    params: dict[str, Any] = {"pageSize": PAGE_SIZE, "columns": ",".join(columns)}
    rows: list[dict[str, Any]] = []
    page, pages, total = 1, 1, 0
    while page <= pages:
        response = client._get_response(path, params={**params, "page": page})
        batch = response.json()
        if page == 1:
            pages = int(response.headers["Result-Pages"])
            total = int(response.headers["Result-Total"])
        if not batch:
            break
        rows += batch
        page += 1
    unique, dropped = dq.dedupe_by_id(rows)
    absent = dq.check_projection(unique, columns)
    return Fetched(unique, total, dropped, absent)


def current_total(client: SimproClient, path: str) -> int:
    """A collection's ``Result-Total`` now, from one 1-row page."""
    response = client._get_response(
        path, params={"page": 1, "pageSize": 1, "columns": "ID"}
    )
    return int(response.headers["Result-Total"])


def report_dir(root: Path, today: date) -> Path:
    """``<root>/<date>``, or ``<date>-2``, ``-3``… if that run already exists."""
    candidate = root / today.isoformat()
    suffix = 2
    while candidate.exists():
        candidate = root / f"{today.isoformat()}-{suffix}"
        suffix += 1
    return candidate


def describe(name: str, fetched: Fetched, total_at_end: int | None = None) -> str:
    """A summary line about one fetch: counts and field names only."""
    line = (
        f"{name}: {len(fetched.rows)} rows; Result-Total at start "
        f"{fetched.total_at_start}"
    )
    if total_at_end is not None:
        drift = total_at_end - fetched.total_at_start
        line += f", at end {total_at_end} (drift {drift:+d})"
    line += f"; repeated rows dropped {fetched.dropped}"
    partial = {k: v for k, v in fetched.absent.items() if v}
    if partial:
        line += f"; rows missing a key (treated as blank): {partial}"
    return line


def collect(
    client: SimproClient, settings: SimproSettings, writer: dq.ReportWriter
) -> dq.Snapshot:
    """Fetch everything the checks need, cheapest and riskiest first.

    Every projection is checked before the ~6,500-request asset scan starts,
    so an ignored column stops the run in its first minute.
    """
    service, projects = settings.company_id_service, settings.company_id_projects
    snap = dq.Snapshot()
    ends: list[tuple[str, Fetched, str]] = []

    def take(name: str, path: str, columns: Sequence[str]) -> list[dict[str, Any]]:
        fetched = fetch_all(client, path, columns)
        ends.append((name, fetched, path))
        return fetched.rows

    snap.sites = take("sites", f"/companies/{service}/sites/", SITE_COLUMNS)
    other = take(
        "sites (projects company, IDs)", f"/companies/{projects}/sites/", ["ID"]
    )
    snap.other_company_site_ids = {row["ID"] for row in other}
    snap.company_customers = take(
        "company customers",
        f"/companies/{service}/customers/companies/",
        COMPANY_CUSTOMER_COLUMNS,
    )
    snap.individual_customers = take(
        "individual customers",
        f"/companies/{service}/customers/individuals/",
        INDIVIDUAL_CUSTOMER_COLUMNS,
    )
    summary = take("customer summary", f"/companies/{service}/customers/", ["ID"])
    snap.summary_customer_ids = {row["ID"] for row in summary}
    snap.summary_customer_total = ends[-1][1].total_at_start
    for role, company_id in (("service", service), ("projects", projects)):
        for kind, columns in (("jobs", JOB_COLUMNS), ("quotes", QUOTE_COLUMNS)):
            rows = take(f"{kind} ({role})", f"/companies/{company_id}/{kind}/", columns)
            getattr(snap, kind).extend({**row, "_company": role} for row in rows)

    asset_rows = 0
    for site in snap.sites:
        path = f"/companies/{service}/sites/{site['ID']}/assets/"
        rows = _assets(client, path)
        snap.assets[site["ID"]] = rows
        asset_rows += len(rows)

    for name, fetched, path in ends:
        writer.note(describe(name, fetched, current_total(client, path)))
    writer.note(f"assets: {asset_rows} rows across {len(snap.assets)} sites")
    _, skipped = dq.s3c_groups(snap.sites)
    writer.note(f"S3c: {skipped} name blocks too large for fuzzy matching")
    return snap


def _assets(client: SimproClient, path: str) -> list[dict[str, Any]]:
    """One site's assets. Absent keys are only checked across the whole scan.

    A site with one asset that happens to omit ``ParentID`` must not abort
    the run, so :func:`fetch_all`'s per-collection projection check is not
    applied per site.
    """
    params: dict[str, Any] = {
        "pageSize": PAGE_SIZE,
        "columns": ",".join(ASSET_COLUMNS),
    }
    rows: list[dict[str, Any]] = []
    page, pages = 1, 1
    while page <= pages:
        response = client._get_response(path, params={**params, "page": page})
        batch = response.json()
        if page == 1:
            pages = int(response.headers["Result-Pages"])
        if not batch:
            break
        rows += batch
        page += 1
    return dq.dedupe_by_id(rows)[0]


@pytest.fixture(scope="module")
def audit(request: pytest.FixtureRequest) -> Iterator[tuple[dq.Snapshot, Any]]:
    """Fetch the snapshot once and open the private report.

    Any failure is reported by exception type only, never by message (which
    can name the build's host or echo a value), and stamps the summary
    ``INCOMPLETE``.
    """
    if os.environ.get("SIMPRO_DATA_AUDIT") != "1":
        pytest.skip("the data audit is opt-in: set SIMPRO_DATA_AUDIT=1")
    settings: SimproSettings = request.getfixturevalue("live_settings")
    writer = dq.ReportWriter(report_dir(AUDIT_ROOT, date.today()))
    requests = 0

    def count(_: httpx.Request) -> None:
        nonlocal requests
        requests += 1

    failure = None
    snap = dq.Snapshot()
    try:
        with open_client(settings) as client:
            client._http.event_hooks["request"].append(count)
            snap = collect(client, settings, writer)
            assets = [a for rows in snap.assets.values() for a in rows]
            dq.check_projection(assets, ASSET_COLUMNS)
    except dq.ProjectionError as exc:
        writer.record_error("FETCH", str(exc))
        failure = "fetch stopped: a requested column was not returned"
    except Exception as exc:  # noqa: BLE001 (reported by type only)
        writer.record_error("FETCH", type(exc).__name__)
        failure = f"fetch failed: {type(exc).__name__}"
    finally:
        logging.getLogger("simpro_client").disabled = False
        writer.note(f"API requests sent: {requests}")
    if failure:
        pytest.fail(failure, pytrace=False)
    yield snap, writer
    writer.finish(dq.CHECKS)


@pytest.mark.parametrize("check", list(dq.CHECKS))
def test_data_quality(audit: tuple[dq.Snapshot, dq.ReportWriter], check: str):
    """One check: findings to the private report, the count to the terminal."""
    snap, writer = audit
    error = None
    try:
        findings = dq.CHECKS[check](snap)
    except dq.ProjectionError as exc:
        writer.record_error(check, str(exc))
        error = f"{check}: could not run ({exc})"
    except Exception as exc:  # noqa: BLE001 (reported by type only)
        writer.record_error(check, type(exc).__name__)
        error = f"{check}: could not run ({type(exc).__name__})"
    if error:
        pytest.fail(error, pytrace=False)
    writer.write_check(check, findings)
    if findings:
        pytest.fail(f"{check}: {len(findings)} findings", pytrace=False)


# Offline checks of the fetch helpers: respx only, so they also run in the
# default suite (as the guard tests in test_live_contract.py do).


@pytest.fixture
def offline_client(mock_settings: SimproSettings, respx_mock) -> SimproClient:
    respx_mock.post(mock_settings.token_url).mock(
        return_value=httpx.Response(
            200, json={"access_token": "t", "token_type": "Bearer", "expires_in": 3600}
        )
    )
    return SimproClient(settings=mock_settings)


def _page(rows: list[dict], pages: int, total: int) -> httpx.Response:
    headers = {
        "Result-Pages": str(pages),
        "Result-Total": str(total),
        "Result-Count": str(len(rows)),
    }
    return httpx.Response(200, json=rows, headers=headers)


def test_fetch_all_pages_dedupes_and_projects(offline_client, respx_mock):
    url = f"{offline_client._settings.base_url}/companies/1/sites/"
    route = respx_mock.get(url).mock(
        side_effect=[
            _page([{"ID": 1, "Name": "a"}, {"ID": 2, "Name": "b"}], 2, 3),
            _page([{"ID": 2, "Name": "b"}, {"ID": 3}], 2, 3),
        ]
    )
    fetched = fetch_all(offline_client, "/companies/1/sites/", ["ID", "Name"])

    assert [row["ID"] for row in fetched.rows] == [1, 2, 3]
    assert (fetched.total_at_start, fetched.dropped) == (3, 1)
    assert fetched.absent == {"ID": 0, "Name": 1}
    assert route.call_count == 2
    params = route.calls[0].request.url.params
    assert (params["pageSize"], params["columns"], params["page"]) == (
        "250",
        "ID,Name",
        "1",
    )


def test_fetch_all_stops_on_an_empty_page(offline_client, respx_mock):
    url = f"{offline_client._settings.base_url}/companies/1/sites/"
    route = respx_mock.get(url).mock(
        side_effect=[_page([{"ID": 1}], 5, 5), _page([], 5, 5)]
    )
    fetched = fetch_all(offline_client, "/companies/1/sites/", ["ID"])

    assert len(fetched.rows) == 1
    assert route.call_count == 2


def test_fetch_all_rejects_an_ignored_column(offline_client, respx_mock):
    url = f"{offline_client._settings.base_url}/companies/1/sites/"
    respx_mock.get(url).mock(return_value=_page([{"ID": 1}], 1, 1))
    with pytest.raises(dq.ProjectionError):
        fetch_all(offline_client, "/companies/1/sites/", ["ID", "Customers"])


def test_fetch_all_needs_paging_headers(offline_client, respx_mock):
    url = f"{offline_client._settings.base_url}/companies/1/sites/"
    respx_mock.get(url).mock(return_value=httpx.Response(200, json=[{"ID": 1}]))
    with pytest.raises(KeyError):
        fetch_all(offline_client, "/companies/1/sites/", ["ID"])


def test_report_dir_never_reuses_a_run(tmp_path: Path):
    today = date(2026, 11, 3)
    assert report_dir(tmp_path, today) == tmp_path / "2026-11-03"
    (tmp_path / "2026-11-03").mkdir()
    (tmp_path / "2026-11-03-2").mkdir()
    assert report_dir(tmp_path, today) == tmp_path / "2026-11-03-3"


def test_report_root_is_git_ignored():
    """The real report root is ignored, so a run can never stage results."""
    dq.ensure_git_ignored(AUDIT_ROOT / "2026-11-03")
