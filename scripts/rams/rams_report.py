#!/usr/bin/env python
"""Daily RAMS document check: which upcoming Simpro jobs lack an RA or an MS.

Reads CVC's live Simpro build (GET only) for every job scheduled from today to
today + ``RAMS_WINDOW_DAYS`` (Europe/London) in the two configured companies.
For each job it lists the attachment **file names** and reports whether a Risk
Assessment and a Method Statement are among them. File contents are never
requested: only the job's attachment *list* route is called, with
``columns=ID,Filename``; the detail route, ``/view/``, ``display=Base64`` and
the zipped-folder download are never used.

The CSV report goes to ``$RAMS_REPORT_DIR`` (outside the repository; mode 700
directory, mode 600 file), named ``rams_report_YYYY-MM-DD.csv``. Console and
log output hold counts, timings, company labels, job IDs and error class names
only, never a customer, site or file name, or the report's path (root
``CLAUDE.md`` §9).

Governance: a side task, not CLIVE development. It imports ``simpro_client``
directly, a narrow, read-only exception to ADR-009's single-gateway rule that
Alex approved on 2026-11-25 (``docs/known-issues.md``). It must not grow into a
service.

Usage:
    RAMS_REPORT_DIR=/path/outside/repo uv run python scripts/rams/rams_report.py

Simpro credentials come from ``SimproSettings`` (``SIMPRO_*`` in the
environment or ``.env``), and ``SIMPRO_COMPANY_ID_SERVICE`` and
``SIMPRO_COMPANY_ID_PROJECTS`` must both be set explicitly.

Scheduling (Alex installs this; Claude Code does not), for example a crontab
line for the account that owns the report directory::

    40 6 * * * cd /path/to/CLIVE-I && RAMS_REPORT_DIR=/path/outside/repo \
        /path/to/uv run python scripts/rams/rams_report.py >> /path/to/rams.log 2>&1

Exit codes: 0 done, 1 done but some Simpro calls failed (the report is still
written, failed jobs carry status ``ERROR``), 2 invalid configuration (nothing
is requested or written).
"""

from __future__ import annotations

import csv
import io
import logging
import os
import re
import sys
import tempfile
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AliasChoices, Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from simpro_client import CustomerRef, Job, SimproClient, SimproSettings
from simpro_client.exceptions import SimproError

REPO_ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger("clive.rams")

#: The only columns the script ever asks Simpro for. Attachment metadata is
#: limited to the file name; nothing here can return file content.
SCHEDULE_COLUMNS = ("ID", "Type", "Reference", "Date")
JOB_COLUMNS = ("ID", "Customer", "Site")
ATTACHMENT_COLUMNS = ("ID", "Filename")

CSV_HEADER = (
    "job_no",
    "company",
    "site",
    "client_name",
    "scheduled_date",
    "ra",
    "ms",
    "status",
    "doc_count",
    "doc_names",
)
STATUSES = ("BOTH", "RA_ONLY", "MS_ONLY", "NONE", "ERROR")

#: Separators folded to a space before matching, so "Risk_Assessment-v2" and
#: "Method.Statement" read like the spaced form.
_SEPARATORS = re.compile(r"[_\-.]+")
#: Characters that make a spreadsheet treat a cell as a formula.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


class RamsSettings(BaseSettings):
    """Report configuration, read from the environment and ``.env``.

    ``.env`` is looked up in the working directory, like ``SimproSettings``,
    so run the script from the repository root.
    """

    model_config = SettingsConfigDict(
        env_prefix="RAMS_",
        env_file=".env",
        extra="ignore",
        validate_by_name=True,
    )

    report_dir: Path = Field(
        description="Directory for the CSV report; must be outside the repo."
    )
    window_days: int = Field(
        default=7,
        ge=0,
        le=31,
        description="Days after today to include; 7 means today to today + 7.",
    )
    timezone: str = Field(
        default="Europe/London", description="Zone that decides what 'today' is."
    )
    ra_pattern: str = Field(
        default=r"risk\s*ass?ess?m[ae]nt",
        description="Case-insensitive regex for a Risk Assessment file name.",
    )
    ms_pattern: str = Field(
        default=r"meth?o[ds]\s*state?ment",
        description="Case-insensitive regex for a Method Statement file name.",
    )
    company_id_service: int = Field(
        validation_alias=AliasChoices("SIMPRO_COMPANY_ID_SERVICE"),
        description="CVC's Service company ID (no default outside the mock).",
    )
    company_id_projects: int = Field(
        validation_alias=AliasChoices("SIMPRO_COMPANY_ID_PROJECTS"),
        description="CVC's Projects company ID (no default outside the mock).",
    )

    @field_validator("ra_pattern", "ms_pattern")
    @classmethod
    def _compiles(cls, value: str) -> str:
        """Reject a pattern that is not a valid regular expression."""
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError("not a valid regular expression") from exc
        return value

    @field_validator("timezone")
    @classmethod
    def _known_zone(cls, value: str) -> str:
        """Reject a zone name the system's tz database does not know."""
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown time zone") from exc
        return value

    def companies(self) -> list[tuple[str, int]]:
        """Return ``(label, company_id)`` for the two configured companies."""
        return [
            ("Service", self.company_id_service),
            ("Projects", self.company_id_projects),
        ]


@dataclass
class JobRow:
    """One report row: a scheduled job and what its file names show."""

    company: str
    company_id: int
    job_id: int
    dates: set[date] = field(default_factory=set)
    site: str = ""
    client_name: str = ""
    ra: bool = False
    ms: bool = False
    matched: list[str] = field(default_factory=list)
    error: bool = False

    @property
    def status(self) -> str:
        """``ERROR``, ``BOTH``, ``RA_ONLY``, ``MS_ONLY`` or ``NONE``."""
        if self.error:
            return "ERROR"
        if self.ra and self.ms:
            return "BOTH"
        if self.ra:
            return "RA_ONLY"
        if self.ms:
            return "MS_ONLY"
        return "NONE"

    def sort_key(self) -> tuple[date, str, int]:
        """Order by first scheduled date, then company, then job number."""
        return (min(self.dates), self.company, self.job_id)

    def as_csv(self) -> list[str]:
        """Render the row in ``CSV_HEADER`` order, formula-safe."""
        values = [
            str(self.job_id),
            self.company,
            self.site,
            self.client_name,
            ";".join(d.isoformat() for d in sorted(self.dates)),
            "Y" if self.ra else "N",
            "Y" if self.ms else "N",
            self.status,
            str(len(self.matched)),
            "; ".join(self.matched),
        ]
        return [safe_cell(v) for v in values]


@dataclass
class RunStats:
    """Counts for the console summary. Holds no Simpro values."""

    schedules_seen: int = 0
    out_of_window: int = 0
    bad_reference: int = 0
    company_errors: int = 0


# --- Pure helpers ---------------------------------------------------------------


def window(today: date, days: int) -> tuple[date, date]:
    """Return the inclusive ``(start, end)`` date window."""
    return today, today + timedelta(days=days)


def today_in(zone: str, now: Callable[[ZoneInfo], datetime] | None = None) -> date:
    """Return today's date in ``zone``; ``now`` is a seam for tests."""
    tz = ZoneInfo(zone)
    current = now(tz) if now else datetime.now(tz)
    return current.astimezone(tz).date()


def normalise_filename(name: str) -> str:
    """Fold separators to spaces so the patterns see words."""
    return _SEPARATORS.sub(" ", name)


def classify(name: str, ra: re.Pattern[str], ms: re.Pattern[str]) -> tuple[bool, bool]:
    """Return ``(is_ra, is_ms)`` for one file name; a RAMS file can be both."""
    text = normalise_filename(name)
    return bool(ra.search(text)), bool(ms.search(text))


def compile_pattern(pattern: str) -> re.Pattern[str]:
    """Compile a configured pattern case-insensitively."""
    return re.compile(pattern, re.IGNORECASE)


def job_id_from_reference(reference: str) -> int | None:
    """Return the job ID from a job schedule's ``"<jobID>-<costCentreID>"``."""
    head = reference.split("-", 1)[0].strip()
    return int(head) if head.isdigit() else None


def client_name(customer: CustomerRef | None) -> str:
    """Company name, or given + family name for an individual customer."""
    if customer is None:
        return ""
    if customer.company_name:
        return customer.company_name.strip()
    parts = (customer.given_name or "", customer.family_name or "")
    return " ".join(p.strip() for p in parts if p and p.strip())


def safe_cell(value: str) -> str:
    """Prefix ``'`` to a cell a spreadsheet would read as a formula."""
    return "'" + value if value.startswith(_FORMULA_PREFIXES) else value


def render_csv(rows: Iterable[JobRow]) -> str:
    """Render the header and rows as CSV text."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_HEADER)
    for row in rows:
        writer.writerow(row.as_csv())
    return buffer.getvalue()


def inside_repo(path: Path) -> bool:
    """Report whether ``path`` resolves to somewhere inside the repository."""
    return path.resolve().is_relative_to(REPO_ROOT)


def write_report(report_dir: Path, run_date: date, content: str) -> None:
    """Write the report atomically with mode 600 in a mode-700 directory.

    The directory is created (mode 700) when missing. The file is written to
    a temporary file in the same directory and renamed over any earlier
    report for the same day, so a reader never sees a half-written file.
    """
    if not report_dir.exists():
        report_dir.mkdir(mode=0o700, parents=True)
        os.chmod(report_dir, 0o700)
    target = report_dir / f"rams_report_{run_date.isoformat()}.csv"
    fd, tmp = tempfile.mkstemp(dir=report_dir, prefix=".rams_report_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            os.fchmod(fh.fileno(), 0o600)
            fh.write(content)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _error_label(exc: BaseException) -> str:
    """Name an error by class and status code only, never its message."""
    status = getattr(exc, "status_code", None)
    return f"{type(exc).__name__}" + (f" status={status}" if status else "")


# --- Simpro reads ---------------------------------------------------------------


def collect_jobs(
    client: SimproClient,
    settings: RamsSettings,
    start: date,
    end: date,
    stats: RunStats,
) -> dict[tuple[str, int], JobRow]:
    """Group the window's job schedules by ``(company, job_id)``.

    ``Date`` and ``Type`` are sent as Simpro filters, and are checked again
    here, because Simpro ignores filter fields it does not know (ADR-015).
    """
    jobs: dict[tuple[str, int], JobRow] = {}
    filters = {
        "Date": f"between({start.isoformat()},{end.isoformat()})",
        "Type": "job",
    }
    for label, company_id in settings.companies():
        try:
            for schedule in client.schedules.iter_all(
                company_id=company_id,
                filters=filters,
                columns=list(SCHEDULE_COLUMNS),
                page_size=250,
            ):
                stats.schedules_seen += 1
                if schedule.type != "job":
                    continue
                if schedule.date is None or not start <= schedule.date <= end:
                    stats.out_of_window += 1
                    continue
                job_id = job_id_from_reference(schedule.reference)
                if job_id is None:
                    stats.bad_reference += 1
                    continue
                row = jobs.setdefault(
                    (label, job_id),
                    JobRow(company=label, company_id=company_id, job_id=job_id),
                )
                row.dates.add(schedule.date)
        except (SimproError, ValidationError) as exc:
            stats.company_errors += 1
            logger.error("company=%s schedules failed: %s", label, _error_label(exc))
    return jobs


def fill_job(
    client: SimproClient,
    row: JobRow,
    ra: re.Pattern[str],
    ms: re.Pattern[str],
) -> None:
    """Add site, client and RA/MS findings to ``row``; mark it on failure."""
    try:
        job: Job = client.jobs.get(
            row.job_id, company_id=row.company_id, columns=list(JOB_COLUMNS)
        )
        row.site = (job.site.name or "").strip() if job.site else ""
        row.client_name = client_name(job.customer)
        for attachment in client.attachments.iter_all(
            company_id=row.company_id,
            job_id=row.job_id,
            columns=list(ATTACHMENT_COLUMNS),
            page_size=250,
        ):
            is_ra, is_ms = classify(attachment.filename, ra, ms)
            row.ra |= is_ra
            row.ms |= is_ms
            if is_ra or is_ms:
                row.matched.append(attachment.filename)
    except (SimproError, ValidationError) as exc:
        row.error = True
        logger.error(
            "company=%s job=%d failed: %s", row.company, row.job_id, _error_label(exc)
        )


# --- Run ------------------------------------------------------------------------


def run(settings: RamsSettings, client: SimproClient, run_date: date) -> int:
    """Build and write the report for ``run_date``; return the exit code."""
    started = time.monotonic()
    start, end = window(run_date, settings.window_days)
    ra, ms = compile_pattern(settings.ra_pattern), compile_pattern(settings.ms_pattern)
    stats = RunStats()

    jobs = collect_jobs(client, settings, start, end, stats)
    rows = sorted(jobs.values(), key=JobRow.sort_key)
    for row in rows:
        fill_job(client, row, ra, ms)

    write_report(settings.report_dir, run_date, render_csv(rows))

    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row.status] += 1
    logger.info(
        "window=%s..%s jobs=%d both=%d ra_only=%d ms_only=%d none=%d error=%d "
        "schedules=%d out_of_window=%d bad_reference=%d company_errors=%d "
        "duration=%.1fs",
        start.isoformat(),
        end.isoformat(),
        len(rows),
        counts["BOTH"],
        counts["RA_ONLY"],
        counts["MS_ONLY"],
        counts["NONE"],
        counts["ERROR"],
        stats.schedules_seen,
        stats.out_of_window,
        stats.bad_reference,
        stats.company_errors,
        time.monotonic() - started,
    )
    return 1 if counts["ERROR"] or stats.company_errors else 0


def _invalid_fields(exc: ValidationError) -> str:
    """Name the invalid settings without echoing their values."""
    return ", ".join(sorted({str(e["loc"][0]) for e in exc.errors() if e["loc"]}))


def main(argv: list[str] | None = None) -> int:
    """Load settings, check them and run the report."""
    if argv:
        print(__doc__, file=sys.stderr)
        return 2
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    try:
        settings = RamsSettings()
    except ValidationError as exc:
        logger.error("missing or invalid settings: %s", _invalid_fields(exc))
        return 2
    if inside_repo(settings.report_dir):
        logger.error("RAMS_REPORT_DIR must be outside the repository")
        return 2
    try:
        simpro_settings = SimproSettings()
    except ValidationError as exc:
        logger.error("missing or invalid Simpro settings: %s", _invalid_fields(exc))
        return 2
    run_date = today_in(settings.timezone)
    with SimproClient(settings=simpro_settings) as client:
        logging.getLogger("simpro_client").setLevel(logging.WARNING)
        return run(settings, client, run_date)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
