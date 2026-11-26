"""Offline tests for the daily RAMS document check (``scripts/rams/rams_report.py``).

Simpro is faked with ``respx``; every company, job, customer, site and file
name here is invented. Nothing contacts live Simpro, and the report is written
to ``tmp_path`` only.
"""

from __future__ import annotations

import csv
import importlib.util
import logging
import re
import stat
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import httpx
import pytest
import respx

from simpro_client import CustomerRef, SimproClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "rams" / "rams_report.py"
_spec = importlib.util.spec_from_file_location("rams_report", SCRIPT_PATH)
rams = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["rams_report"] = rams
_spec.loader.exec_module(rams)  # type: ignore[union-attr]

SERVICE, PROJECTS, OTHER = 10, 20, 30
RUN_DATE = date(2026, 11, 25)

SECRET_COMPANY_CUSTOMER = "Zebra Holdings plc"
SECRET_GIVEN, SECRET_FAMILY = "Quentin", "Xylophone"
SECRET_SITE = "Zebra Warehouse Unit 9"
SECRET_FILES = (
    "Zebra Risk Assesment v2.pdf",
    "Zebra_Method-Statement.docx",
    "Zebra RAMS Risk Assessment and Method Statement.pdf",
    "Zebra site photo.jpg",
)
INJECTION_CUSTOMER = "=HYPERLINK(evil)"

#: Request paths the fake answers with a 503, set per test.
FAILING_PATHS: set[str] = set()


# --- Pure helpers ---------------------------------------------------------------

RA = rams.compile_pattern(r"risk\s*ass?ess?m[ae]nt")
MS = rams.compile_pattern(r"meth?o[ds]\s*state?ment")


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Risk Assessment.pdf", (True, False)),
        ("risk assessment.pdf", (True, False)),
        ("RISK ASSESSMENT.PDF", (True, False)),
        ("Risk Assesment.pdf", (True, False)),
        ("Risk Asessment.pdf", (True, False)),
        ("Risk Assessmant.pdf", (True, False)),
        ("RiskAssessment.pdf", (True, False)),
        ("Risk_Assessment-v2.pdf", (True, False)),
        ("Method Statement.pdf", (False, True)),
        ("method statement.docx", (False, True)),
        ("Methos Statement.pdf", (False, True)),
        ("Metod Statement.pdf", (False, True)),
        ("Method Statment.pdf", (False, True)),
        ("Method_Statement.pdf", (False, True)),
        ("Method.Statement.pdf", (False, True)),
        ("RAMS - Risk Assessment & Method Statement.pdf", (True, True)),
        ("Risk.pdf", (False, False)),
        ("Assessment form.pdf", (False, False)),
        ("Statement of works.pdf", (False, False)),
        ("RAMS.pdf", (False, False)),
        ("photo.jpg", (False, False)),
    ],
)
def test_classify_matches_spellings_and_rejects_near_misses(name, expected):
    """The default patterns catch common misspellings and nothing unrelated."""
    assert rams.classify(name, RA, MS) == expected


@pytest.mark.parametrize(
    ("ra", "ms", "error", "status"),
    [
        (True, True, False, "BOTH"),
        (True, False, False, "RA_ONLY"),
        (False, True, False, "MS_ONLY"),
        (False, False, False, "NONE"),
        (True, True, True, "ERROR"),
    ],
)
def test_status_mapping(ra, ms, error, status):
    """Each RA/MS combination maps to one status; a failure wins."""
    row = rams.JobRow("Service", SERVICE, 1, {RUN_DATE}, ra=ra, ms=ms, error=error)
    assert row.status == status


@pytest.mark.parametrize(
    ("utc_now", "expected"),
    [
        # 00:30 UTC on the morning BST starts is still 00:30 GMT in London.
        (datetime(2026, 3, 29, 0, 30, tzinfo=UTC), date(2026, 3, 29)),
        # 23:30 UTC the night before BST ends is already 00:30 BST next day.
        (datetime(2026, 10, 24, 23, 30, tzinfo=UTC), date(2026, 10, 25)),
        # In summer, 23:30 UTC is 00:30 BST the next day.
        (datetime(2026, 7, 1, 23, 30, tzinfo=UTC), date(2026, 7, 2)),
        # In winter, London is on UTC.
        (datetime(2026, 12, 1, 23, 30, tzinfo=UTC), date(2026, 12, 1)),
    ],
)
def test_today_follows_europe_london_across_dst(utc_now, expected):
    """'Today' is the Europe/London date, not the UTC one."""
    assert rams.today_in("Europe/London", lambda _tz: utc_now) == expected


def test_window_is_inclusive_today_to_plus_days():
    """A 7-day setting covers today and the seven days after it."""
    assert rams.window(RUN_DATE, 7) == (date(2026, 11, 25), date(2026, 12, 2))


@pytest.mark.parametrize(
    ("customer", "expected"),
    [
        (CustomerRef(CompanyName="Acme Ltd", Type="Company"), "Acme Ltd"),
        (CustomerRef(GivenName="Ada", FamilyName="Lovelace"), "Ada Lovelace"),
        (CustomerRef(CompanyName="", GivenName="Ada", FamilyName=None), "Ada"),
        (None, ""),
    ],
)
def test_client_name_handles_company_and_individual(customer, expected):
    """Company customers use CompanyName; individuals use given + family."""
    assert rams.client_name(customer) == expected


@pytest.mark.parametrize(
    ("reference", "expected"),
    [("123-45", 123), ("123", 123), ("abc-1", None), ("", None)],
)
def test_job_id_from_reference(reference, expected):
    """Job schedules carry '<jobID>-<costCentreID>' in Reference."""
    assert rams.job_id_from_reference(reference) == expected


@pytest.mark.parametrize("value", ["=1+1", "+1", "-1", "@SUM(A1)", "\tx"])
def test_formula_cells_are_escaped(value):
    """Cells a spreadsheet would evaluate get a leading apostrophe."""
    assert rams.safe_cell(value) == "'" + value


def test_inside_repo_detection(tmp_path):
    """Paths in the repository are refused; tmp_path is not inside it."""
    assert rams.inside_repo(REPO_ROOT / "docs" / "reports")
    assert not rams.inside_repo(tmp_path)


# --- Fake Simpro ----------------------------------------------------------------


def _schedule(sid: int, kind: str, reference: str, day: str) -> dict[str, Any]:
    return {"ID": sid, "Type": kind, "Reference": reference, "Date": day}


SCHEDULES = {
    SERVICE: [
        _schedule(1, "job", "101-1", "2026-11-25"),
        _schedule(2, "job", "101-2", "2026-11-27"),  # same job, second date
        _schedule(3, "job", "101-1", "2026-11-25"),  # same job and date again
        _schedule(4, "activity", "7", "2026-11-26"),  # not a job
        _schedule(5, "job", "102-1", "2026-11-26"),
        _schedule(6, "job", "103-1", "2026-12-10"),  # outside the window
        _schedule(7, "job", "bad", "2026-11-26"),  # unparseable reference
    ],
    PROJECTS: [
        _schedule(8, "job", "201-3", "2026-12-02"),  # last day of the window
        _schedule(9, "job", "202-3", "2026-11-28"),  # job fetch fails
        _schedule(10, "job", "203-3", "2026-11-25"),  # no attachments
    ],
}

JOBS = {
    (SERVICE, 101): {
        "Customer": {"CompanyName": SECRET_COMPANY_CUSTOMER, "Type": "Company"},
        "Site": {"ID": 1, "Name": SECRET_SITE},
    },
    (SERVICE, 102): {
        "Customer": {"GivenName": SECRET_GIVEN, "FamilyName": SECRET_FAMILY},
        "Site": {"ID": 2, "Name": SECRET_SITE},
    },
    (PROJECTS, 201): {
        "Customer": {"CompanyName": INJECTION_CUSTOMER},
        "Site": {"ID": 3, "Name": SECRET_SITE},
    },
    (PROJECTS, 203): {
        "Customer": {"CompanyName": SECRET_COMPANY_CUSTOMER},
        "Site": {"ID": 4, "Name": SECRET_SITE},
    },
}

ATTACHMENTS = {
    (SERVICE, 101): [SECRET_FILES[0], SECRET_FILES[1], SECRET_FILES[3]],
    (SERVICE, 102): [SECRET_FILES[0]],
    (PROJECTS, 201): [SECRET_FILES[2]],
    (PROJECTS, 203): [],
}


def _paged(items: list[dict[str, Any]], params: dict[str, list[str]]) -> httpx.Response:
    """Serve one page of ``items`` with Simpro's Result-* headers."""
    size = int(params.get("pageSize", ["30"])[0])
    page = int(params.get("page", ["1"])[0])
    pages = max(1, -(-len(items) // size))
    chunk = items[(page - 1) * size : page * size]
    headers = {
        "Result-Total": str(len(items)),
        "Result-Count": str(len(chunk)),
        "Result-Pages": str(pages),
    }
    return httpx.Response(200, json=chunk, headers=headers)


def _simpro(request: httpx.Request) -> httpx.Response:
    """Route a request to the invented data above."""
    path = request.url.path.removeprefix("/api/v1.0")
    params = parse_qs(urlsplit(str(request.url)).query)
    if path in FAILING_PATHS:
        return httpx.Response(503)
    if m := re.fullmatch(r"/companies/(\d+)/schedules/", path):
        return _paged(SCHEDULES.get(int(m[1]), []), params)
    if m := re.fullmatch(r"/companies/(\d+)/jobs/(\d+)", path):
        key = (int(m[1]), int(m[2]))
        if key not in JOBS:
            return httpx.Response(500, json={"errors": [{"message": "boom"}]})
        body = {
            "ID": key[1],
            "Description": "x",
            "Total": {"ExTax": 1, "Tax": 0, "IncTax": 1},
        }
        return httpx.Response(200, json={**body, **JOBS[key]})
    if m := re.fullmatch(r"/companies/(\d+)/jobs/(\d+)/attachments/files/", path):
        names = ATTACHMENTS.get((int(m[1]), int(m[2])), [])
        items = [{"ID": str(i), "Filename": n} for i, n in enumerate(names)]
        return _paged(items, params)
    return httpx.Response(404)


@pytest.fixture
def fake_simpro(mock_settings):
    """Yield the respx router and a client wired to it."""
    with respx.mock(assert_all_called=False) as router:
        router.post(mock_settings.token_url).mock(
            return_value=httpx.Response(
                200, json={"access_token": "tok", "expires_in": 3600}
            )
        )
        router.route(host=urlsplit(mock_settings.base_url).hostname).mock(
            side_effect=_simpro
        )
        # A large bucket so the run never waits on the real clock (tests §4).
        fast = mock_settings.model_copy(
            update={"limiter_capacity": 10_000, "limiter_refill_rate": 10_000.0}
        )
        with SimproClient(settings=fast) as client:
            client._sleep = lambda _seconds: None
            yield router, client


@pytest.fixture
def settings(tmp_path):
    """Report settings that ignore any real ``.env`` and environment."""
    return rams.RamsSettings(
        _env_file=None,
        report_dir=tmp_path / "private" / "rams",
        company_id_service=SERVICE,
        company_id_projects=PROJECTS,
    )


def _read_report(settings) -> list[dict[str, str]]:
    path = settings.report_dir / f"rams_report_{RUN_DATE.isoformat()}.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --- End to end -----------------------------------------------------------------


def test_report_rows_and_columns(fake_simpro, settings):
    """One row per scheduled job, sorted, with the agreed columns and values."""
    _router, client = fake_simpro
    assert rams.run(settings, client, RUN_DATE) == 1  # job 202 failed

    rows = _read_report(settings)
    assert list(rows[0]) == list(rams.CSV_HEADER)
    by_job = {(r["company"], r["job_no"]): r for r in rows}
    assert [(r["company"], r["job_no"]) for r in rows] == [
        ("Projects", "203"),
        ("Service", "101"),
        ("Service", "102"),
        ("Projects", "202"),
        ("Projects", "201"),
    ]

    both = by_job[("Service", "101")]
    assert both["scheduled_date"] == "2026-11-25;2026-11-27"
    assert (both["ra"], both["ms"], both["status"]) == ("Y", "Y", "BOTH")
    assert both["doc_count"] == "2"
    assert both["doc_names"] == f"{SECRET_FILES[0]}; {SECRET_FILES[1]}"
    assert both["client_name"] == SECRET_COMPANY_CUSTOMER
    assert both["site"] == SECRET_SITE

    ra_only = by_job[("Service", "102")]
    assert ra_only["status"] == "RA_ONLY"
    assert ra_only["client_name"] == f"{SECRET_GIVEN} {SECRET_FAMILY}"

    combined = by_job[("Projects", "201")]
    assert (combined["status"], combined["doc_count"]) == ("BOTH", "1")
    assert combined["client_name"] == "'" + INJECTION_CUSTOMER

    none = by_job[("Projects", "203")]
    assert (none["ra"], none["ms"], none["status"]) == ("N", "N", "NONE")
    assert (none["doc_count"], none["doc_names"]) == ("0", "")

    error = by_job[("Projects", "202")]
    assert error["status"] == "ERROR"
    assert error["scheduled_date"] == "2026-11-28"


def test_report_file_and_directory_are_private(fake_simpro, settings):
    """The directory is created 700 and the report written 600, nothing else."""
    _router, client = fake_simpro
    rams.run(settings, client, RUN_DATE)
    assert stat.S_IMODE(settings.report_dir.stat().st_mode) == 0o700
    files = list(settings.report_dir.iterdir())
    assert [f.name for f in files] == ["rams_report_2026-11-25.csv"]
    assert stat.S_IMODE(files[0].stat().st_mode) == 0o600


def test_rerun_same_day_replaces_the_report(fake_simpro, settings):
    """A second run the same day overwrites the file and leaves no temp file."""
    _router, client = fake_simpro
    rams.run(settings, client, RUN_DATE)
    rams.run(settings, client, RUN_DATE)
    assert len(list(settings.report_dir.iterdir())) == 1


def test_requests_are_read_only_metadata_only_and_company_scoped(
    fake_simpro, settings, mock_settings
):
    """Only GETs (plus the token POST), no file content, only the two companies."""
    router, client = fake_simpro
    rams.run(settings, client, RUN_DATE)

    assert router.calls, "no requests were made"
    for call in router.calls:
        request = call.request
        url = str(request.url)
        if url == mock_settings.token_url:
            assert request.method == "POST"
            continue
        assert request.method == "GET"
        path = request.url.path.removeprefix("/api/v1.0")
        params = parse_qs(urlsplit(url).query)
        company = int(re.match(r"/companies/(\d+)/", path)[1])
        assert company in (SERVICE, PROJECTS)
        assert company != OTHER
        # Never a single-file, view, folder or zipped download route.
        assert not re.search(r"/attachments/files/[^/]+", path), path
        assert "/view" not in path and "/folders" not in path
        assert "display" not in {k.lower() for k in params}
        assert "zip" not in request.headers.get("accept", "").lower()
        if path.endswith("/attachments/files/"):
            assert params["columns"] == ["ID,Filename"]
        if "/schedules/" in path:
            assert params["Date"] == ["between(2026-11-25,2026-12-02)"]
            assert params["Type"] == ["job"]


def test_output_and_logs_hold_no_client_values(fake_simpro, settings, capsys, caplog):
    """No customer, site, file name or report path reaches stdout, stderr or logs."""
    _router, client = fake_simpro
    caplog.set_level(logging.DEBUG)
    rams.run(settings, client, RUN_DATE)

    captured = capsys.readouterr()
    text = captured.out + captured.err + caplog.text
    assert "jobs=5 both=2 ra_only=1 ms_only=0 none=1 error=1" in caplog.text
    secrets = [
        SECRET_COMPANY_CUSTOMER,
        SECRET_GIVEN,
        SECRET_FAMILY,
        SECRET_SITE,
        INJECTION_CUSTOMER,
        "Zebra",
        "boom",
        str(settings.report_dir),
        *SECRET_FILES,
    ]
    for secret in secrets:
        assert secret not in text, "a client value reached the output"


def test_window_counts_and_ignored_schedules(fake_simpro, settings, caplog):
    """Out-of-window and unparseable schedules are dropped and counted."""
    _router, client = fake_simpro
    caplog.set_level(logging.INFO, logger="clive.rams")
    rams.run(settings, client, RUN_DATE)
    assert "out_of_window=1 bad_reference=1 company_errors=0" in caplog.text


def test_failed_company_is_reported_not_fatal(
    fake_simpro, settings, caplog, monkeypatch
):
    """A schedules failure for one company still writes the other's rows."""
    _router, client = fake_simpro
    monkeypatch.setattr(
        sys.modules[__name__], "FAILING_PATHS", {f"/companies/{PROJECTS}/schedules/"}
    )
    caplog.set_level(logging.INFO, logger="clive.rams")
    assert rams.run(settings, client, RUN_DATE) == 1
    rows = _read_report(settings)
    assert {r["company"] for r in rows} == {"Service"}
    assert "company=Projects schedules failed: SimproServerError" in caplog.text


# --- Configuration --------------------------------------------------------------


def test_main_refuses_report_dir_inside_repo(monkeypatch, tmp_path, caplog):
    """A report directory inside the repository stops the run before any request."""
    monkeypatch.chdir(tmp_path)  # no .env here
    monkeypatch.setenv("RAMS_REPORT_DIR", str(REPO_ROOT / "reports"))
    monkeypatch.setenv("SIMPRO_COMPANY_ID_SERVICE", str(SERVICE))
    monkeypatch.setenv("SIMPRO_COMPANY_ID_PROJECTS", str(PROJECTS))
    with respx.mock(assert_all_called=False) as router:
        assert rams.main([]) == 2
        assert not router.calls
    assert "outside the repository" in caplog.text
    assert not (REPO_ROOT / "reports").exists()


def test_main_names_missing_settings_without_values(monkeypatch, tmp_path, caplog):
    """Missing company IDs fail with exit 2 and name the fields only."""
    monkeypatch.chdir(tmp_path)
    for var in ("SIMPRO_COMPANY_ID_SERVICE", "SIMPRO_COMPANY_ID_PROJECTS"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("RAMS_REPORT_DIR", str(tmp_path / "out"))
    assert rams.main([]) == 2
    assert "SIMPRO_COMPANY_ID_SERVICE" in caplog.text
    assert str(tmp_path) not in caplog.text


def test_invalid_pattern_is_rejected(tmp_path):
    """A pattern that is not a valid regex is a configuration error."""
    with pytest.raises(ValueError):
        rams.RamsSettings(
            _env_file=None,
            report_dir=tmp_path,
            company_id_service=SERVICE,
            company_id_projects=PROJECTS,
            ra_pattern="risk(",
        )
