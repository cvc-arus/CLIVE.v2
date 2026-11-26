#!/usr/bin/env python
"""Daily RAMS document check: which upcoming Simpro jobs lack an RA or an MS.

Reads CVC's live Simpro build (GET only) for every job scheduled from today to
today + ``RAMS_WINDOW_DAYS`` (Europe/London) in the two configured companies.
For each job it lists the attachment **file names** and reports whether a Risk
Assessment and a Method Statement are among them. File contents are never
requested: only the job's attachment *list* route is called, with
``columns=ID,Filename``; the detail route, ``/view/``, ``display=Base64`` and
the zipped-folder download are never used.

The report is an Excel workbook (``.xlsx``, one sheet, written with the
standard library only) in ``$RAMS_REPORT_DIR`` (outside the repository; mode
700 directory, mode 600 file), named ``rams_report_YYYY-MM-DD.xlsx``. Every
text cell is an inline string, so no cell is ever evaluated as a formula.
Console and log output hold counts, timings, company labels, job IDs and error
class names only, never a customer, site or file name, or the report's path
(root ``CLAUDE.md`` §9).

If a company's schedules cannot be read, the report carries an ``ERROR`` row
for that company, so a reader can see that its jobs may be missing.

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
written; failed jobs and companies carry status ``ERROR``), 2 invalid
configuration (nothing is requested or written).
"""

from __future__ import annotations

import io
import logging
import os
import re
import stat
import sys
import tempfile
import time
import zipfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from xml.sax.saxutils import escape
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

HEADER = (
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
    "note",
)
STATUSES = ("BOTH", "RA_ONLY", "MS_ONLY", "NONE", "ERROR")

JOB_ERROR_NOTE = "job details or attachments could not be read"
COMPANY_ERROR_NOTE = "schedules could not be read; this company's jobs may be missing"

#: Errors that mark a job or company as failed instead of stopping the run.
#: ``ValueError`` covers a response body that is not JSON (``JSONDecodeError``)
#: and pydantic's ``ValidationError``.
READ_ERRORS = (SimproError, ValueError)

#: Separators folded to a space before matching, so "Risk_Assessment-v2" and
#: "Method.Statement" read like the spaced form.
_SEPARATORS = re.compile(r"[_\-.]+")

#: Characters XML 1.0 does not allow; one of them would corrupt the workbook.
_XML_ILLEGAL = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff￾￿]")
#: Excel's limit on the characters in one cell.
_MAX_CELL_CHARS = 32767
#: A fixed timestamp for the workbook's zip entries.
_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
_SHEET_NAME = "RAMS"

_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
_XML_DECL = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml"

_CONTENT_TYPES = (
    _XML_DECL
    + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" '
    'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    f'<Override PartName="/xl/workbook.xml" ContentType="{_CT}.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" '
    f'ContentType="{_CT}.worksheet+xml"/>'
    f'<Override PartName="/xl/styles.xml" ContentType="{_CT}.styles+xml"/>'
    "</Types>"
)
_ROOT_RELS = (
    _XML_DECL + f'<Relationships xmlns="{_NS_PKG_REL}">'
    f'<Relationship Id="rId1" Type="{_NS_REL}/officeDocument" '
    'Target="xl/workbook.xml"/>'
    "</Relationships>"
)
_WORKBOOK_RELS = (
    _XML_DECL + f'<Relationships xmlns="{_NS_PKG_REL}">'
    f'<Relationship Id="rId1" Type="{_NS_REL}/worksheet" '
    'Target="worksheets/sheet1.xml"/>'
    f'<Relationship Id="rId2" Type="{_NS_REL}/styles" Target="styles.xml"/>'
    "</Relationships>"
)
#: Style 0 is the default; style 1 is bold, for the header row.
_STYLES = (
    _XML_DECL + f'<styleSheet xmlns="{_NS_MAIN}">'
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    "</fonts>"
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/>'
    "</border></borders>"
    '<cellStyleXfs count="1">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" '
    'applyFont="1"/>'
    "</cellXfs>"
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
    "</cellStyles>"
    "</styleSheet>"
)

Cell = str | int


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
        description="Directory for the report; must be outside the repo."
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

    def as_cells(self) -> list[Cell]:
        """Render the row in ``HEADER`` order; numbers stay numbers."""
        return [
            self.job_id,
            self.company,
            self.site,
            self.client_name,
            ";".join(d.isoformat() for d in sorted(self.dates)),
            "Y" if self.ra else "N",
            "Y" if self.ms else "N",
            self.status,
            len(self.matched),
            "; ".join(self.matched),
            JOB_ERROR_NOTE if self.error else "",
        ]


@dataclass
class RunStats:
    """Counts for the console summary. Holds no Simpro values."""

    schedules_seen: int = 0
    out_of_window: int = 0
    bad_reference: int = 0
    failed_companies: list[str] = field(default_factory=list)

    @property
    def company_errors(self) -> int:
        """How many companies' schedules could not be read."""
        return len(self.failed_companies)


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
    """Return the job ID from a job schedule's ``"<jobID>-<costCentreID>"``.

    Only ASCII digits count: ``str.isdigit`` also accepts characters such as
    superscripts, which ``int`` rejects.
    """
    head = reference.split("-", 1)[0].strip()
    return int(head) if head.isascii() and head.isdigit() else None


def client_name(customer: CustomerRef | None) -> str:
    """Company name, or given + family name for an individual customer."""
    if customer is None:
        return ""
    if customer.company_name:
        return customer.company_name.strip()
    parts = (customer.given_name or "", customer.family_name or "")
    return " ".join(p.strip() for p in parts if p and p.strip())


def company_error_cells(label: str) -> list[Cell]:
    """Render the row that flags a company whose schedules failed."""
    cells: list[Cell] = ["" for _ in HEADER]
    cells[HEADER.index("company")] = label
    cells[HEADER.index("status")] = "ERROR"
    cells[HEADER.index("note")] = COMPANY_ERROR_NOTE
    return cells


def _column_letter(index: int) -> str:
    """Return the spreadsheet column name for a 0-based index (0 -> ``A``)."""
    letters = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(ord("A") + rem) + letters
    return letters


def _cell_xml(ref: str, value: Cell, style: int) -> str:
    """Render one cell: a number, or an inline string that is never a formula."""
    style_attr = f' s="{style}"' if style else ""
    if isinstance(value, int) and not isinstance(value, bool):
        return f'<c r="{ref}"{style_attr}><v>{value}</v></c>'
    text = escape(_XML_ILLEGAL.sub("", str(value))[:_MAX_CELL_CHARS])
    return (
        f'<c r="{ref}"{style_attr} t="inlineStr">'
        f'<is><t xml:space="preserve">{text}</t></is></c>'
    )


def render_xlsx(rows: Iterable[Sequence[Cell]]) -> bytes:
    """Render ``HEADER`` and ``rows`` as a one-sheet ``.xlsx`` workbook.

    The header is bold and frozen, with an auto-filter over the whole table.
    The zip entries carry a fixed timestamp, so the same rows give the same
    bytes.
    """
    all_rows: list[Sequence[Cell]] = [HEADER, *rows]
    last_col = _column_letter(len(HEADER) - 1)
    last_ref = f"{last_col}{len(all_rows)}"
    row_xml = []
    for r, values in enumerate(all_rows, start=1):
        style = 1 if r == 1 else 0
        cells = "".join(
            _cell_xml(f"{_column_letter(c)}{r}", v, style) for c, v in enumerate(values)
        )
        row_xml.append(f'<row r="{r}">{cells}</row>')
    sheet = (
        _XML_DECL + f'<worksheet xmlns="{_NS_MAIN}" xmlns:r="{_NS_REL}">'
        f'<dimension ref="A1:{last_ref}"/>'
        '<sheetViews><sheetView workbookViewId="0">'
        '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
        "</sheetView></sheetViews>"
        f"<sheetData>{''.join(row_xml)}</sheetData>"
        f'<autoFilter ref="A1:{last_ref}"/>'
        "</worksheet>"
    )
    workbook = (
        _XML_DECL + f'<workbook xmlns="{_NS_MAIN}" xmlns:r="{_NS_REL}">'
        f'<sheets><sheet name="{_SHEET_NAME}" sheetId="1" r:id="rId1"/></sheets>'
        "<definedNames>"
        '<definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">'
        f"'{_SHEET_NAME}'!$A$1:${last_col}${len(all_rows)}</definedName>"
        "</definedNames>"
        "</workbook>"
    )
    parts = {
        "[Content_Types].xml": _CONTENT_TYPES,
        "_rels/.rels": _ROOT_RELS,
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": _WORKBOOK_RELS,
        "xl/styles.xml": _STYLES,
        "xl/worksheets/sheet1.xml": sheet,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, text in parts.items():
            info = zipfile.ZipInfo(name, date_time=_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, text.encode("utf-8"))
    return buffer.getvalue()


def inside_repo(path: Path) -> bool:
    """Report whether ``path`` resolves to somewhere inside the repository."""
    return path.resolve().is_relative_to(REPO_ROOT)


def report_dir_problem(path: Path) -> str | None:
    """Return why ``path`` cannot hold the report, or ``None`` if it can.

    A missing directory is fine (``write_report`` creates it with mode 700).
    An existing one must be a directory that only its owner can read, because
    file names and dates in it are visible to anyone who can list it. The
    script does not change the mode of a directory it did not create.
    """
    if not path.exists():
        return None
    if not path.is_dir():
        return "RAMS_REPORT_DIR exists and is not a directory"
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        return "RAMS_REPORT_DIR must not be readable by group or others (chmod 700)"
    return None


def write_report(report_dir: Path, run_date: date, content: bytes) -> None:
    """Write the report atomically with mode 600 in a mode-700 directory.

    The directory is created (mode 700) when missing. The file is written to
    a temporary file in the same directory and renamed over any earlier
    report for the same day, so a reader never sees a half-written file.
    """
    if not report_dir.exists():
        report_dir.mkdir(mode=0o700, parents=True)
        os.chmod(report_dir, 0o700)
    target = report_dir / f"rams_report_{run_date.isoformat()}.xlsx"
    fd, tmp = tempfile.mkstemp(dir=report_dir, prefix=".rams_report_", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
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
    A company whose schedules fail is recorded in ``stats.failed_companies``;
    rows already read for it are kept.
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
        except READ_ERRORS as exc:
            stats.failed_companies.append(label)
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
    except READ_ERRORS as exc:
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

    cells = [company_error_cells(label) for label in stats.failed_companies]
    cells += [row.as_cells() for row in rows]
    write_report(settings.report_dir, run_date, render_xlsx(cells))

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
    if problem := report_dir_problem(settings.report_dir):
        logger.error(problem)
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
