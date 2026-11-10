#!/usr/bin/env python
"""Run CLIVE's evaluation set through Open WebUI and record the answers.

Course correction W4 T3 (``docs/sprints/course-correction/W4-evaluation.md``);
design and file format in ``evaluation/README.md``.

Each question is sent to Open WebUI's ``POST /api/chat/completions`` with the
knowledge collection attached, as a user's chat would be, without a chat id,
so no chat history is saved. Per question the runner records the answer, the
cited sources, latency, token usage and marking aids (``must_include`` groups
found, source groups cited, distractors present). Alex marks each answer.

The questions and answers are CVC content (ADR-017): the eval set and the
results are git-ignored, results are written with mode 0600, and the console
and log show question ids, categories, counts, timings and HTTP status only,
never questions, answers or source names (root ``CLAUDE.md`` §9).

Usage:
    uv run python scripts/eval/run_eval.py [--ids L01,M01] [--limit N]
    uv run python scripts/eval/run_eval.py --summarise evaluation/results/<file>.json

Configuration (``.env``, prefix ``EVAL_``): ``EVAL_OPENWEBUI_URL``,
``EVAL_API_KEY``, ``EVAL_KNOWLEDGE_ID``, ``EVAL_MODEL``,
``EVAL_TIMEOUT_SECONDS``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import statistics
import subprocess
import sys
import time
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import yaml
from pydantic import SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EVAL_SET = REPO_ROOT / "evaluation" / "eval-set.yaml"
RESULTS_DIR = REPO_ROOT / "evaluation" / "results"

CATEGORIES = ("lookup", "multi_doc", "not_found")
MARKS = ("correct", "partly", "wrong", "hallucinated")

#: Retrieval settings recorded per run. The config endpoint also returns other
#: services' API keys, so only these keys are kept (allow-list, never a deny-list).
RAG_SETTING_KEYS = (
    "TOP_K",
    "TOP_K_RERANKER",
    "RELEVANCE_THRESHOLD",
    "RAG_FULL_CONTEXT",
    "BYPASS_EMBEDDING_AND_RETRIEVAL",
    "ENABLE_RAG_HYBRID_SEARCH",
    "ENABLE_RAG_HYBRID_SEARCH_ENRICHED_TEXTS",
    "HYBRID_BM25_WEIGHT",
    "RAG_RERANKING_ENGINE",
    "RAG_RERANKING_MODEL",
    "TEXT_SPLITTER",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "CONTENT_EXTRACTION_ENGINE",
    "PDF_EXTRACT_IMAGES",
)
EMBEDDING_SETTING_KEYS = ("RAG_EMBEDDING_ENGINE", "RAG_EMBEDDING_MODEL")

logger = logging.getLogger("clive.eval")


class EvalSettings(BaseSettings):
    """Runner configuration, read from the environment and ``.env``."""

    model_config = SettingsConfigDict(
        env_prefix="EVAL_", env_file=REPO_ROOT / ".env", extra="ignore"
    )

    openwebui_url: str = "http://127.0.0.1:3000"
    api_key: SecretStr
    knowledge_id: str
    model: str
    timeout_seconds: float = 300.0


class EvalSetError(ValueError):
    """The eval set is malformed. Messages name ids and fields, never values."""


# --- Eval set -----------------------------------------------------------------


def _is_str_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _is_groups(value: Any) -> bool:
    return isinstance(value, list) and all(_is_str_list(g) and g for g in value)


def validate_questions(data: Any) -> list[dict[str, Any]]:
    """Check the eval set's structure and return its questions.

    Raises ``EvalSetError`` listing every problem by question id (or position)
    and field name.
    """
    if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
        raise EvalSetError("top level must be a mapping with a 'questions' list")
    problems: list[str] = []
    seen: set[str] = set()
    for position, question in enumerate(data["questions"], start=1):
        if not isinstance(question, dict):
            problems.append(f"#{position}: not a mapping")
            continue
        qid = question.get("id")
        ref = qid if isinstance(qid, str) and qid else f"#{position}"
        for field in ("id", "question", "reference_answer"):
            value = question.get(field)
            if not isinstance(value, str) or not value.strip():
                problems.append(f"{ref}: '{field}' must be a non-empty string")
        if not isinstance(question.get("source_locator", ""), str):
            problems.append(f"{ref}: 'source_locator' must be a string")
        if question.get("category") not in CATEGORIES:
            problems.append(f"{ref}: 'category' must be one of {', '.join(CATEGORIES)}")
        for field in ("must_include", "source_groups"):
            if not _is_groups(question.get(field, [])):
                problems.append(
                    f"{ref}: '{field}' must be a list of non-empty string lists"
                )
        if not _is_str_list(question.get("distractors", [])):
            problems.append(f"{ref}: 'distractors' must be a list of strings")
        if isinstance(qid, str) and qid:
            if qid in seen:
                problems.append(f"{ref}: duplicate id")
            seen.add(qid)
    if problems:
        raise EvalSetError("; ".join(problems))
    return data["questions"]


def load_eval_set(path: Path) -> list[dict[str, Any]]:
    """Read and validate the eval set YAML file."""
    return validate_questions(yaml.safe_load(path.read_text(encoding="utf-8")))


def select_questions(
    questions: list[dict[str, Any]], ids: list[str] | None, limit: int | None
) -> list[dict[str, Any]]:
    """Return the questions to run: the given ids in file order, then the limit."""
    if ids:
        unknown = sorted(set(ids) - {q["id"] for q in questions})
        if unknown:
            raise EvalSetError(f"unknown id(s): {', '.join(unknown)}")
        questions = [q for q in questions if q["id"] in ids]
    if limit is None:
        return questions
    if limit < 1:
        raise EvalSetError("limit must be at least 1")
    return questions[:limit]


# --- Marking aids ---------------------------------------------------------------


def normalise_text(text: str) -> str:
    """Lower-case and drop commas and all whitespace for fact matching.

    Removing spaces lets ``60 mm`` match ``60mm`` and ``IP 68`` match ``IP68``.
    """
    return re.sub(r"[\s,]", "", text.lower())


def normalise_name(name: str) -> str:
    """Normalise a file name to its lower-case letters and digits.

    Open WebUI stores upload names with punctuation and spacing changed (for
    example ``&`` becomes ``_``), so only letters and digits are compared.
    """
    return re.sub(r"[^a-z0-9]", "", name.lower())


def term_in_text(term: str, text: str) -> bool:
    """Return whether ``term`` appears in ``text``, as a fact rather than a fragment.

    Case, commas and whitespace are ignored, as in ``normalise_text``. A term
    that starts or ends with a digit must not continue into a longer number, so
    ``60mm`` is not found in ``160mm`` or ``2.60mm``, nor ``IP6`` in ``IP68``.
    An empty term is never found.
    """
    chars = normalise_text(term)
    if not chars:
        return False
    before = r"(?<!\d)(?<!\d[.,])" if chars[0].isdecimal() else ""
    after = r"(?!\d)(?![.,]\d)" if chars[-1].isdecimal() else ""
    body = r"[\s,]*".join(re.escape(c) for c in chars)
    return re.search(before + body + after, text.lower()) is not None


def groups_found(answer: str, groups: list[list[str]]) -> int:
    """Count ``must_include`` groups with at least one alternative in the answer."""
    return sum(1 for group in groups if any(term_in_text(a, answer) for a in group))


def _same_file(expected: str, cited: str) -> bool:
    """Match file names on letters and digits, with or without the extension."""
    full = normalise_name(expected) == normalise_name(cited)
    stems = normalise_name(Path(expected).stem) == normalise_name(Path(cited).stem)
    return full or stems


def source_groups_hit(cited_names: list[str], groups: list[list[str]]) -> int:
    """Count source groups with at least one file among the cited sources."""
    return sum(
        1
        for group in groups
        if any(_same_file(e, c) for e in group for c in cited_names)
    )


def distractors_present(answer: str, distractors: list[str]) -> int:
    """Count distractors (known wrong facts) that appear in the answer."""
    return sum(1 for d in distractors if term_in_text(d, answer))


# --- Open WebUI ---------------------------------------------------------------


def _get_json_object(client: httpx.Client, path: str) -> dict[str, Any]:
    """GET ``path`` and return its JSON object.

    Raises ``ValueError`` when the body is not JSON or not an object (for
    example an HTML login page served with status 200).
    """
    data = client.get(path).raise_for_status().json()
    if not isinstance(data, dict):
        raise ValueError(f"{path}: response is not a JSON object")
    return data


def settings_snapshot(client: httpx.Client) -> dict[str, Any]:
    """Record the Open WebUI version and the allow-listed retrieval settings.

    Raises ``ValueError`` when a response is not a JSON object.
    """
    version = _get_json_object(client, "/api/version").get("version")
    rag = _get_json_object(client, "/api/v1/retrieval/config")
    embedding = _get_json_object(client, "/api/v1/retrieval/embedding")
    template = rag.get("RAG_TEMPLATE")
    template = template if isinstance(template, str) else ""
    return {
        "openwebui_version": version,
        "retrieval": {k: rag.get(k) for k in RAG_SETTING_KEYS},
        "rag_template_sha256": hashlib.sha256(template.encode()).hexdigest()[:12],
        "embedding": {k: embedding.get(k) for k in EMBEDDING_SETTING_KEYS},
    }


def extract_sources(raw: Any) -> list[dict[str, Any]]:
    """Return the cited files: name, file id and per-chunk distances; no chunk text.

    With a knowledge collection attached, Open WebUI v0.12.3 returns one source
    item for the whole collection (``source`` holds only the collection's ``id``
    and ``type``). The file of each retrieved chunk is in ``metadata[i]``
    (``name``, ``file_id``), aligned with ``document[i]`` and ``distances[i]``.
    Chunks are grouped by file in first-seen order.
    """
    files: dict[str, dict[str, Any]] = {}
    for item in raw if isinstance(raw, list) else []:
        if not isinstance(item, dict):
            continue
        source = item.get("source") if isinstance(item.get("source"), dict) else {}
        metadata = (
            item.get("metadata") if isinstance(item.get("metadata"), list) else []
        )
        distances = (
            item.get("distances") if isinstance(item.get("distances"), list) else []
        )
        chunks = metadata or [{}]
        for index, meta in enumerate(chunks):
            meta = meta if isinstance(meta, dict) else {}
            name = meta.get("name") or source.get("name")
            file_id = meta.get("file_id") or source.get("id")
            key = str(file_id or name)
            entry = files.setdefault(
                key, {"name": name, "file_id": file_id, "distances": []}
            )
            if index < len(distances):
                entry["distances"].append(distances[index])
    return list(files.values())


def ask(
    client: httpx.Client, settings: EvalSettings, question: dict[str, Any]
) -> dict[str, Any]:
    """Send one question and return its result record."""
    body = {
        "model": settings.model,
        "messages": [{"role": "user", "content": question["question"]}],
        "files": [{"type": "collection", "id": settings.knowledge_id}],
        "stream": False,
    }
    record: dict[str, Any] = {
        "id": question["id"],
        "category": question["category"],
        "status": "error",
        "http_status": None,
        "answer": None,
        "sources": [],
        "usage": None,
        "error": None,
    }
    started = time.monotonic()
    try:
        response = client.post("/api/chat/completions", json=body)
        record["http_status"] = response.status_code
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if content is not None and not isinstance(content, str):
            raise TypeError("answer content is not text")
        record["answer"] = content or ""
        record["sources"] = extract_sources(data.get("sources"))
        record["usage"] = data.get("usage")
        if record["answer"].strip():
            record["status"] = "ok"
        else:  # e.g. a thinking model that spent its whole budget reasoning
            record["status"] = "empty"
            record["error"] = "empty answer"
    except httpx.HTTPStatusError as exc:
        record["error"] = f"HTTP {exc.response.status_code}"
    except Exception as exc:  # any failure: record the type only, never a message
        record["error"] = type(exc).__name__
    record["seconds"] = round(time.monotonic() - started, 1)

    answer = record["answer"] or ""
    cited = [s["name"] for s in record["sources"] if s["name"]]
    record["aids"] = {
        "must_include_found": groups_found(answer, question.get("must_include", [])),
        "must_include_total": len(question.get("must_include", [])),
        "source_groups_hit": source_groups_hit(
            cited, question.get("source_groups", [])
        ),
        "source_groups_total": len(question.get("source_groups", [])),
        "distractors_present": distractors_present(
            answer, question.get("distractors", [])
        ),
    }
    record["mark"] = ""
    record["marker_notes"] = ""
    return record


# --- Output -------------------------------------------------------------------


def is_git_ignored(path: Path) -> bool:
    """Return whether git ignores both output file types in the folder ``path``.

    Works before the folder exists.
    """
    cwd = next(p for p in [path, *path.parents] if p.exists())
    for probe in (path / "probe.json", path / "probe.md"):
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(probe)],
            cwd=cwd,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return False
    return True


def write_private(path: Path, content: str, *, replace: bool = False) -> None:
    """Write ``path`` with mode 0600; refuse to overwrite unless ``replace``.

    An existing file being replaced is set to 0600 as well, and a symbolic
    link at ``path`` is refused (``OSError``) rather than followed.
    """
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    flags |= os.O_TRUNC if replace else os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        os.fchmod(fh.fileno(), 0o600)
        fh.write(content)


def results_path(results_dir: Path, model: str, today: str) -> Path:
    """Return a new results file path; a second run the same day gets ``_2``..."""
    stem = f"{today}_{re.sub(r'[^A-Za-z0-9._-]+', '-', model)}"
    path = results_dir / f"{stem}.json"
    n = 2
    while path.exists():
        path = results_dir / f"{stem}_{n}.json"
        n += 1
    return path


def git_commit() -> str:
    """Return the repository's short commit hash, or ``unknown``."""
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() or "unknown"


def summary_markdown(results: dict[str, Any]) -> str:
    """Build the value-free summary: run details and per-category counts only."""
    run = results["run"]
    records = results["records"]
    lines = [
        f"# Evaluation run {run['date']}",
        "",
        f"- Model: `{run['model']}`",
        f"- Open WebUI: {run['settings']['openwebui_version']}",
        f"- Runner commit: `{run['runner_commit']}`",
        f"- Eval set SHA-256: `{run['eval_set_sha256'][:12]}`"
        f" ({run['questions_run']} of {run['questions_total']} questions)",
        "",
        "## Settings",
        "",
        "| Setting | Value |",
        "|---|---|",
    ]
    settings = run["settings"]
    for key, value in {**settings["embedding"], **settings["retrieval"]}.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.append(f"| RAG template SHA-256 | `{settings['rag_template_sha256']}` |")

    lines += [
        "",
        "## Results by category (marking aids)",
        "",
        "| Category | Questions | Answered | Errors | Facts found | "
        "Source groups cited | With distractors | Median s |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for category in (*CATEGORIES, "all"):
        rows = [r for r in records if category in ("all", r["category"])]
        if not rows:
            continue
        ok = [r for r in rows if r["status"] == "ok"]
        aids = [r["aids"] for r in rows]
        facts = f"{sum(a['must_include_found'] for a in aids)}/" + str(
            sum(a["must_include_total"] for a in aids)
        )
        cited = f"{sum(a['source_groups_hit'] for a in aids)}/" + str(
            sum(a["source_groups_total"] for a in aids)
        )
        distract = sum(1 for a in aids if a["distractors_present"])
        median = statistics.median(r["seconds"] for r in ok) if ok else "-"
        lines.append(
            f"| {category} | {len(rows)} | {len(ok)} | {len(rows) - len(ok)} | "
            f"{facts} | {cited} | {distract} | {median} |"
        )

    marks = Counter((r["category"], r.get("mark") or "unmarked") for r in records)
    if any(m != "unmarked" for _, m in marks):
        columns = (*MARKS, "unmarked", "invalid")
        lines += [
            "",
            "## Marks",
            "",
            "| Category | " + " | ".join(columns) + " |",
            "|---|" + "---|" * len(columns),
        ]
        for category in (*CATEGORIES, "all"):
            rows = [r for r in records if category in ("all", r["category"])]
            if not rows:
                continue
            counts = Counter(
                (r.get("mark") or "unmarked")
                if (r.get("mark") or "unmarked") in (*MARKS, "unmarked")
                else "invalid"
                for r in rows
            )
            lines.append(
                f"| {category} | " + " | ".join(str(counts[c]) for c in columns) + " |"
            )
    return "\n".join(lines) + "\n"


# --- Commands -----------------------------------------------------------------


def run(
    settings: EvalSettings,
    eval_set: Path,
    results_dir: Path,
    ids: list[str] | None = None,
    limit: int | None = None,
    transport: httpx.BaseTransport | None = None,
) -> int:
    """Run the selected questions; return the exit code (0 ok, 1 errors, 2 setup)."""
    if not is_git_ignored(results_dir):
        logger.error("results folder is not git-ignored; refusing to write")
        return 2
    try:
        questions = load_eval_set(eval_set)
        selected = select_questions(questions, ids, limit)
    except (OSError, yaml.YAMLError) as exc:
        logger.error("cannot read the eval set: %s", type(exc).__name__)
        return 2
    except EvalSetError as exc:
        logger.error("eval set problems: %s", exc)
        return 2

    headers = {"Authorization": f"Bearer {settings.api_key.get_secret_value()}"}
    with httpx.Client(
        base_url=settings.openwebui_url,
        headers=headers,
        timeout=settings.timeout_seconds,
        transport=transport,
    ) as client:
        try:
            snapshot = settings_snapshot(client)
        except httpx.HTTPStatusError as exc:
            logger.error("settings snapshot: HTTP %s", exc.response.status_code)
            return 2
        except httpx.HTTPError as exc:
            logger.error("Open WebUI not reachable: %s", type(exc).__name__)
            return 2
        except ValueError as exc:  # not JSON, or not a JSON object
            logger.error(
                "settings snapshot: unexpected response (%s)", type(exc).__name__
            )
            return 2
        logger.info(
            "Open WebUI %s; %d of %d questions",
            snapshot["openwebui_version"],
            len(selected),
            len(questions),
        )
        records = []
        for question in selected:
            record = ask(client, settings, question)
            records.append(record)
            aids = record["aids"]
            logger.info(
                "%5s  %-9s  %-5s  http=%s  %6.1fs  cited=%d  facts=%d/%d"
                "  sources=%d/%d  distractors=%d%s",
                record["id"],
                record["category"],
                record["status"],
                record["http_status"],
                record["seconds"],
                len(record["sources"]),
                aids["must_include_found"],
                aids["must_include_total"],
                aids["source_groups_hit"],
                aids["source_groups_total"],
                aids["distractors_present"],
                f"  {record['error']}" if record["error"] else "",
            )

    today = date.today().isoformat()
    results = {
        "run": {
            "date": today,
            "runner_commit": git_commit(),
            "model": settings.model,
            "knowledge_id": settings.knowledge_id,
            "eval_set_sha256": hashlib.sha256(eval_set.read_bytes()).hexdigest(),
            "questions_total": len(questions),
            "questions_run": len(selected),
            "settings": snapshot,
        },
        "records": records,
    }
    results_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = results_path(results_dir, settings.model, today)
    write_private(path, json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    write_private(path.with_suffix(".md"), summary_markdown(results))
    errors = sum(1 for r in records if r["status"] != "ok")
    logger.info(
        "ok: %d, errors: %d; written to %s",
        len(records) - errors,
        errors,
        path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path,
    )
    return 1 if errors else 0


def summarise(path: Path) -> int:
    """Rebuild the Markdown summary of a (marked) results file."""
    if not is_git_ignored(path.resolve().parent):
        logger.error("results folder is not git-ignored; refusing to write")
        return 2
    try:
        results = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("cannot read the results file: %s", type(exc).__name__)
        return 2
    try:
        summary = summary_markdown(results)
        marks = Counter(r.get("mark") or "unmarked" for r in results["records"])
    except (KeyError, TypeError, AttributeError) as exc:  # hand-edited file
        logger.error("results file has an unexpected structure: %s", type(exc).__name__)
        return 2
    try:
        write_private(path.with_suffix(".md"), summary, replace=True)
    except OSError as exc:
        logger.error("cannot write the summary: %s", type(exc).__name__)
        return 2
    logger.info("summary rewritten; marks: %s", dict(sorted(marks.items())))
    return 0


def _positive_int(value: str) -> int:
    """Parse a command-line integer that must be at least 1."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and run or summarise."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--ids", help="comma-separated question ids to run")
    parser.add_argument(
        "--limit", type=_positive_int, help="run at most this many questions"
    )
    parser.add_argument(
        "--summarise",
        type=Path,
        metavar="RESULTS_JSON",
        help="rebuild the summary of a marked results file instead of running",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    if args.summarise:
        return summarise(args.summarise)
    try:
        settings = EvalSettings()
    except ValidationError as exc:
        fields = sorted({str(e["loc"][0]).upper() for e in exc.errors() if e["loc"]})
        logger.error(
            "missing or invalid settings: %s", ", ".join(f"EVAL_{f}" for f in fields)
        )
        return 2
    ids = [i.strip() for i in args.ids.split(",") if i.strip()] if args.ids else None
    return run(settings, args.eval_set, args.results_dir.resolve(), ids, args.limit)


if __name__ == "__main__":
    sys.exit(main())
