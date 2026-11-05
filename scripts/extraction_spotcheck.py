#!/usr/bin/env python
"""Run files through Tika as Open WebUI does and measure the extraction.

Course correction W3 T3 (``docs/sprints/course-correction/W3-kb-audit.md``).
Each file in a folder is sent to the existing Tika container twice:

- ``PUT /tika/text`` with the file's MIME type, the call Open WebUI's
  ``TikaLoader`` makes (v0.12.3, inline-image extraction off). Its text is
  what the knowledge base would index, so it is saved and counted.
- ``PUT /tika/html`` for the XHTML, to count pages, empty pages, tables and
  headings, which plain text cannot show.

Files are labelled ``F1``, ``F2``... in file-name order. Output goes to the
git-ignored private store (ADR-017), ``docs/simpro/private/kb-extraction/<date>/``:

- ``labels.md``: label to file name and type. Never read by Claude Code.
- ``text/<label>.txt``: the extracted text. Never read by Claude Code.
- ``metrics.json``: labels, types, numbers and parser names only.

The console shows labels, counts and ok/error only, never file names or
text, and errors are reported by exception type only. Alex runs this script;
Claude Code does not (root ``CLAUDE.md`` §9).

Usage:
    uv run python scripts/extraction_spotcheck.py <input folder> [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import time
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "docs" / "simpro" / "private" / "kb-extraction"
DEFAULT_TIKA_URL = "http://127.0.0.1:9998"
#: A page with fewer non-whitespace characters than this counts as empty.
EMPTY_PAGE_CHARS = 20
#: OCR of a scanned multi-page PDF can take minutes.
TIKA_TIMEOUT_SECONDS = 600.0
HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})


def count_chars(text: str) -> int:
    """Count non-whitespace characters, so layout padding does not inflate counts."""
    return sum(1 for ch in text if not ch.isspace())


class XhtmlCounter(HTMLParser):
    """Count pages, per-page characters, tables, table rows and headings.

    Tika wraps each PDF page in ``<div class="page">``; OCR text sits in a
    nested ``<div class="ocr">``, so it counts towards its page. Text in
    ``<head>`` is metadata and is skipped.
    """

    def __init__(self) -> None:
        super().__init__()
        self.page_chars: list[int] = []
        self.tables = 0
        self.table_rows = 0
        self.headings = 0
        self._page_depth = 0
        self._in_head = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track page boundaries and count structural elements."""
        if tag == "head":
            self._in_head = True
        elif tag == "div":
            classes = (dict(attrs).get("class") or "").split()
            if self._page_depth:
                self._page_depth += 1
            elif "page" in classes:
                self._page_depth = 1
                self.page_chars.append(0)
        elif tag == "table":
            self.tables += 1
        elif tag == "tr":
            self.table_rows += 1
        elif tag in HEADING_TAGS:
            self.headings += 1

    def handle_endtag(self, tag: str) -> None:
        """Close the current page when its outermost ``div`` ends."""
        if tag == "head":
            self._in_head = False
        elif tag == "div" and self._page_depth:
            self._page_depth -= 1

    def handle_data(self, data: str) -> None:
        """Add text characters to the current page."""
        if self._page_depth and not self._in_head:
            self.page_chars[-1] += count_chars(data)


def xhtml_metrics(xhtml: str) -> dict[str, int]:
    """Return page, table and heading counts from Tika's XHTML output."""
    counter = XhtmlCounter()
    counter.feed(xhtml)
    counter.close()
    return {
        "page_divs": len(counter.page_chars),
        "empty_pages": sum(1 for n in counter.page_chars if n < EMPTY_PAGE_CHARS),
        "tables": counter.tables,
        "table_rows": counter.table_rows,
        "headings": counter.headings,
    }


def _as_list(value: Any) -> list[str]:
    """Tika returns a single value as a string and repeated values as a list."""
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def _as_int(value: Any) -> int | None:
    """Parse a Tika metadata number, or return ``None`` when absent or invalid."""
    try:
        return int(_as_list(value)[0])
    except (IndexError, ValueError):
        return None


def file_metrics(
    text_meta: dict[str, Any], html_meta: dict[str, Any]
) -> dict[str, Any]:
    """Combine both Tika responses into the numbers-only metrics for one file."""
    structure = xhtml_metrics(str(html_meta.get("X-TIKA:content", "")))
    pages = _as_int(text_meta.get("xmpTPg:NPages")) or structure["page_divs"] or None
    chars = count_chars(str(text_meta.get("X-TIKA:content", "")))
    parsers = [
        p.rsplit(".", 1)[-1] for p in _as_list(text_meta.get("X-TIKA:Parsed-By"))
    ]
    ocr_pages = _as_int(text_meta.get("pdf:ocrPageCount"))
    empty = structure["empty_pages"] if structure["page_divs"] else None
    return {
        "content_type": str(text_meta.get("Content-Type", "")).split(";")[0],
        "pages": pages,
        "chars": chars,
        "chars_per_page": round(chars / pages, 1) if pages else None,
        "empty_pages": empty,
        "empty_page_share": round(empty / pages, 2)
        if pages and empty is not None
        else None,
        "tables": structure["tables"],
        "table_rows": structure["table_rows"],
        "headings": structure["headings"],
        "ocr_used": bool(ocr_pages) or "TesseractOCRParser" in parsers,
        "ocr_pages": ocr_pages,
        "parsers": parsers,
        "tika_warnings": sum(
            1 for k in text_meta if k.startswith(("X-TIKA:EXCEPTION", "X-TIKA:WARN"))
        ),
    }


def is_git_ignored(path: Path) -> bool:
    """Return whether git ignores ``path``; works before the path exists."""
    probe = path / "probe.txt"
    cwd = next(p for p in [path, *path.parents] if p.exists())
    result = subprocess.run(
        ["git", "check-ignore", "-q", str(probe)],
        cwd=cwd,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def write_private(path: Path, content: str) -> None:
    """Create ``path`` with mode 0600; never overwrite an existing file."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(content)


def make_private_dir(path: Path) -> None:
    """Create ``path`` and its missing parents with mode 0700."""
    for parent in reversed([path, *path.parents]):
        if not parent.exists():
            parent.mkdir(mode=0o700)
            parent.chmod(0o700)


def tika_put(client: httpx.Client, endpoint: str, data: bytes, mime: str | None) -> Any:
    """Send one file to a Tika endpoint and return the parsed JSON response."""
    headers = {"Accept": "application/json"}
    if mime:
        headers["Content-Type"] = mime
    response = client.put(endpoint, content=data, headers=headers)
    response.raise_for_status()
    return response.json()


def git_commit() -> str:
    """Return the short commit hash of the repository, or ``unknown``."""
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "unknown"


def run(input_dir: Path, out_dir: Path, tika_url: str) -> int:
    """Extract every file in ``input_dir`` into ``out_dir``; return the exit code."""
    if not input_dir.is_dir():
        print("input folder not found", file=sys.stderr)
        return 2
    if input_dir.resolve().is_relative_to(REPO_ROOT) and not is_git_ignored(
        input_dir.resolve()
    ):
        print(
            "input folder is inside the repository but not git-ignored", file=sys.stderr
        )
        return 2
    if not is_git_ignored(out_dir):
        print("output folder is not git-ignored; refusing to write", file=sys.stderr)
        return 2
    if out_dir.exists():
        print("output folder already exists; pass --out or move it", file=sys.stderr)
        return 2
    files = sorted(
        p for p in input_dir.iterdir() if p.is_file() and not p.name.startswith(".")
    )
    if not files:
        print("no files in the input folder", file=sys.stderr)
        return 2

    with httpx.Client(base_url=tika_url, timeout=TIKA_TIMEOUT_SECONDS) as client:
        try:
            version = client.get("/version").raise_for_status().text.strip()
        except httpx.HTTPError as exc:
            print(f"Tika not reachable: {type(exc).__name__}", file=sys.stderr)
            return 2
        make_private_dir(out_dir / "text")
        print(f"{version}; {len(files)} files")

        labels = ["| Label | File name | Type |", "|---|---|---|"]
        results: list[dict[str, Any]] = []
        for number, path in enumerate(files, start=1):
            label = f"F{number}"
            mime = mimetypes.guess_type(path.name)[0]
            labels.append(
                f"| {label} | {path.name.replace('|', '/')} | {mime or '?'} |"
            )
            record: dict[str, Any] = {"label": label, "size_bytes": path.stat().st_size}
            started = time.monotonic()
            try:
                data = path.read_bytes()
                text_meta = tika_put(client, "/tika/text", data, mime)
                html_meta = tika_put(client, "/tika/html", data, mime)
                record.update(file_metrics(text_meta, html_meta), status="ok")
                text = str(text_meta.get("X-TIKA:content", "")).strip()
                write_private(out_dir / "text" / f"{label}.txt", text)
            except httpx.HTTPStatusError as exc:
                record.update(status="error", error=f"HTTP {exc.response.status_code}")
            except Exception as exc:  # any failure: report the type only, no message
                record.update(status="error", error=type(exc).__name__)
            record["seconds"] = round(time.monotonic() - started, 1)
            results.append(record)
            print(
                f"{label:>4}  {record['status']:<5}  pages={record.get('pages')}  "
                f"chars={record.get('chars')}  "
                f"empty_pages={record.get('empty_pages')}  "
                f"tables={record.get('tables')}  headings={record.get('headings')}  "
                f"ocr={record.get('ocr_used')}  {record.get('error', '')}".rstrip()
            )

    write_private(out_dir / "labels.md", "\n".join(labels) + "\n")
    metrics = {
        "run": {
            "date": date.today().isoformat(),
            "tika_version": version,
            "script_commit": git_commit(),
            "endpoints": ["PUT /tika/text (as Open WebUI)", "PUT /tika/html"],
            "empty_page_threshold_chars": EMPTY_PAGE_CHARS,
        },
        "files": results,
    }
    write_private(out_dir / "metrics.json", json.dumps(metrics, indent=2) + "\n")
    errors = sum(1 for r in results if r["status"] != "ok")
    print(f"ok: {len(results) - errors}, errors: {errors}; written to {out_dir}")
    return 1 if errors else 0


def main() -> int:
    """Parse arguments and run the spot-check."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "input_dir", type=Path, help="folder holding the files to check"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=OUTPUT_ROOT / date.today().isoformat(),
        help="output folder; must be git-ignored and must not exist",
    )
    parser.add_argument("--tika-url", default=DEFAULT_TIKA_URL, help="Tika server URL")
    args = parser.parse_args()
    return run(args.input_dir, args.out.resolve(), args.tika_url)


if __name__ == "__main__":
    sys.exit(main())
