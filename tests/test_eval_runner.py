"""Offline tests for the evaluation runner (``scripts/eval/run_eval.py``, W4 T3).

Open WebUI is faked with ``respx``; every question, answer and file name here
is invented.
"""

from __future__ import annotations

import importlib.util
import json
import stat
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
import respx

RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "eval" / "run_eval.py"
_spec = importlib.util.spec_from_file_location("run_eval", RUNNER_PATH)
run_eval = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules["run_eval"] = run_eval
_spec.loader.exec_module(run_eval)  # type: ignore[union-attr]

BASE = "http://webui.test"
SECRET_QUESTION = "What is the zebra ladder interval?"
SECRET_ANSWER = "Zebra ladders are inspected every 3 months, not every 6 months."

EVAL_SET_YAML = f"""
version: 1
questions:
  - id: L01
    category: lookup
    question: "{SECRET_QUESTION}"
    reference_answer: Every 3 months.
    must_include: [[3 months, quarterly], [zebra]]
    source_groups: [[Example Policy & Rules.pdf]]
    source_locator: section 2
    distractors: [6 months]
  - id: M01
    category: multi_doc
    question: Which camera fits both specs?
    reference_answer: X200.
    must_include: [[x200]]
    source_groups: [[spec.docx], [datasheet.pdf]]
    source_locator: tables
    distractors: []
  - id: N01
    category: not_found
    question: What is the drone policy?
    reference_answer: Not in the knowledge base.
    must_include: []
    source_groups: []
    source_locator: ""
    distractors: []
"""


@pytest.fixture
def eval_set(tmp_path: Path) -> Path:
    path = tmp_path / "eval-set.yaml"
    path.write_text(EVAL_SET_YAML, encoding="utf-8")
    return path


@pytest.fixture
def settings() -> Any:
    return run_eval.EvalSettings(
        _env_file=None,
        openwebui_url=BASE,
        api_key="test-key-not-real",
        knowledge_id="kb-1",
        model="test-model:1b",
        timeout_seconds=5,
    )


def _fake_webui(router: respx.MockRouter, chat: httpx.Response) -> respx.Route:
    router.get("/api/version").respond(json={"version": "0.12.3"})
    router.get("/api/v1/retrieval/config").respond(
        json={
            "TOP_K": 5,
            "CHUNK_SIZE": 1500,
            "RAG_TEMPLATE": "template text",
            "DATALAB_MARKER_API_KEY": "leaky-secret",
            "web": {"OLLAMA_CLOUD_WEB_SEARCH_API_KEY": "leaky-secret"},
        }
    )
    router.get("/api/v1/retrieval/embedding").respond(
        json={
            "RAG_EMBEDDING_ENGINE": "ollama",
            "RAG_EMBEDDING_MODEL": "nomic-embed-text",
            "openai_config": {"key": "leaky-secret"},
        }
    )
    return router.post("/api/chat/completions").mock(return_value=chat)


def _chat_ok() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [{"message": {"content": SECRET_ANSWER}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            # Shape of Open WebUI v0.12.3 with a collection attached: one item
            # for the collection, the file of each chunk in metadata[i].
            "sources": [
                {
                    "source": {"id": "kb-1", "type": "collection"},
                    "document": [
                        "chunk text that must not be stored",
                        "second chunk",
                        "third chunk",
                    ],
                    "metadata": [
                        {"name": "example policy _ rules.pdf", "file_id": "f1"},
                        {"name": "other.pdf", "file_id": "f2"},
                        {"name": "example policy _ rules.pdf", "file_id": "f1"},
                    ],
                    "distances": [0.8, 0.5, 0.6],
                }
            ],
        },
    )


# --- Eval set validation ----------------------------------------------------


def test_load_eval_set_accepts_the_format(eval_set: Path) -> None:
    questions = run_eval.load_eval_set(eval_set)
    assert [q["id"] for q in questions] == ["L01", "M01", "N01"]


def test_validation_names_ids_and_fields_never_values() -> None:
    data = {
        "questions": [
            {"id": "A1", "category": "secret-category", "question": "q"},
            {"id": "A1", "category": "lookup", "question": "", "reference_answer": "r"},
        ]
    }
    with pytest.raises(run_eval.EvalSetError) as exc:
        run_eval.validate_questions(data)
    message = str(exc.value)
    assert "A1: 'category' must be one of" in message
    assert "A1: duplicate id" in message
    assert "A1: 'question' must be a non-empty string" in message
    assert "secret-category" not in message


def test_validation_rejects_a_bare_list() -> None:
    with pytest.raises(run_eval.EvalSetError, match="'questions' list"):
        run_eval.validate_questions([{"id": "L01"}])


def test_select_questions_by_id_and_limit(eval_set: Path) -> None:
    questions = run_eval.load_eval_set(eval_set)
    assert [
        q["id"] for q in run_eval.select_questions(questions, ["N01", "L01"], None)
    ] == [
        "L01",
        "N01",
    ]
    assert len(run_eval.select_questions(questions, None, 2)) == 2
    with pytest.raises(run_eval.EvalSetError, match="unknown id"):
        run_eval.select_questions(questions, ["X99"], None)


# --- Marking aids -------------------------------------------------------------


def test_groups_found_ignores_case_and_commas() -> None:
    groups = [["1,500 mm", "1.5 m"], ["Zebra"], ["absent"]]
    assert run_eval.groups_found("Height is 1500 MM for the zebra.", groups) == 2


def test_groups_found_ignores_spaces() -> None:
    groups = [["60mm"], ["IP68"], ["ZX9 unit"]]
    assert run_eval.groups_found("Range 60 mm, rated IP 68, zx9unit.", groups) == 3


def test_source_groups_match_ampersand_and_extension() -> None:
    groups = [["Policy & Rules.pdf"], ["spec.docx"], ["other.pdf"]]
    cited = ["policy _ rules.pdf", "SPEC.pdf"]
    assert run_eval.source_groups_hit(cited, groups) == 2


def test_source_names_match_on_letters_and_digits_only() -> None:
    groups = [["Site Survey - Rev B (final).pdf"], ["Rev C.pdf"]]
    cited = ["site_survey_rev_b_final.PDF"]
    assert run_eval.source_groups_hit(cited, groups) == 1


def test_distractors_present() -> None:
    assert run_eval.distractors_present("every 6 Months", ["6 months", "9 months"]) == 1


# --- Open WebUI calls ---------------------------------------------------------


def test_extract_sources_falls_back_to_the_source_item() -> None:
    raw = [{"source": {"id": "f9", "name": "a.pdf"}, "distances": [0.1]}]
    assert run_eval.extract_sources(raw) == [
        {"name": "a.pdf", "file_id": "f9", "distances": [0.1]}
    ]
    assert run_eval.extract_sources(None) == []


@respx.mock(base_url=BASE, assert_all_called=False)
def test_snapshot_keeps_only_allow_listed_settings(
    respx_mock: respx.MockRouter,
) -> None:
    _fake_webui(respx_mock, _chat_ok())
    with httpx.Client(base_url=BASE) as client:
        snapshot = run_eval.settings_snapshot(client)
    assert snapshot["openwebui_version"] == "0.12.3"
    assert snapshot["retrieval"]["TOP_K"] == 5
    assert snapshot["embedding"]["RAG_EMBEDDING_MODEL"] == "nomic-embed-text"
    assert "leaky-secret" not in json.dumps(snapshot)
    assert "template text" not in json.dumps(snapshot)


@respx.mock(base_url=BASE, assert_all_called=False)
def test_ask_sends_collection_without_chat_id(
    respx_mock: respx.MockRouter, settings: Any, eval_set: Path
) -> None:
    route = _fake_webui(respx_mock, _chat_ok())
    question = run_eval.load_eval_set(eval_set)[0]
    with httpx.Client(base_url=BASE) as client:
        record = run_eval.ask(client, settings, question)
    body = json.loads(route.calls.last.request.content)
    assert body["files"] == [{"type": "collection", "id": "kb-1"}]
    assert body["stream"] is False
    assert body["model"] == "test-model:1b"
    assert "chat_id" not in body and "parent_id" not in body
    assert record["status"] == "ok"
    assert record["sources"] == [
        {
            "name": "example policy _ rules.pdf",
            "file_id": "f1",
            "distances": [0.8, 0.6],
        },
        {"name": "other.pdf", "file_id": "f2", "distances": [0.5]},
    ]
    assert record["aids"] == {
        "must_include_found": 2,
        "must_include_total": 2,
        "source_groups_hit": 1,
        "source_groups_total": 1,
        "distractors_present": 1,
    }
    assert record["mark"] == ""


@respx.mock(base_url=BASE, assert_all_called=False)
def test_ask_records_http_errors_and_exception_types(
    respx_mock: respx.MockRouter, settings: Any, eval_set: Path
) -> None:
    question = run_eval.load_eval_set(eval_set)[0]
    route = _fake_webui(respx_mock, httpx.Response(500, text="secret body"))
    with httpx.Client(base_url=BASE) as client:
        assert run_eval.ask(client, settings, question)["error"] == "HTTP 500"
        route.side_effect = httpx.ReadTimeout("secret message")
        record = run_eval.ask(client, settings, question)
    assert record["error"] == "ReadTimeout"
    assert record["status"] == "error"


@respx.mock(base_url=BASE, assert_all_called=False)
def test_ask_counts_an_empty_answer_as_an_error(
    respx_mock: respx.MockRouter, settings: Any, eval_set: Path
) -> None:
    empty = {"choices": [{"message": {"content": "  \n"}}], "sources": []}
    _fake_webui(respx_mock, httpx.Response(200, json=empty))
    question = run_eval.load_eval_set(eval_set)[0]
    with httpx.Client(base_url=BASE) as client:
        record = run_eval.ask(client, settings, question)
    assert record["status"] == "empty"
    assert record["error"] == "empty answer"
    assert record["http_status"] == 200


# --- Full run -----------------------------------------------------------------


def test_run_writes_private_results_and_prints_no_content(
    tmp_path: Path,
    settings: Any,
    eval_set: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(run_eval, "is_git_ignored", lambda _path: True)
    results_dir = tmp_path / "results"
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        _fake_webui(router, _chat_ok())
        caplog.set_level("INFO", logger="clive.eval")
        code = run_eval.run(settings, eval_set, results_dir, ids=["L01", "N01"])
    assert code == 0

    files = sorted(results_dir.iterdir())
    assert [f.suffix for f in files] == [".json", ".md"]
    for f in files:
        assert stat.S_IMODE(f.stat().st_mode) == 0o600
    results = json.loads(files[0].read_text())
    assert [r["id"] for r in results["records"]] == ["L01", "N01"]
    assert results["run"]["questions_total"] == 3
    assert "chunk text" not in files[0].read_text()

    summary = files[1].read_text()
    assert SECRET_QUESTION not in summary and SECRET_ANSWER not in summary
    assert "| lookup | 1 | 1 | 0 | 2/2 | 1/1 | 1 |" in summary

    shown = caplog.text + capsys.readouterr().out
    for value in (SECRET_QUESTION, SECRET_ANSWER, "policy", "test-key-not-real"):
        assert value not in shown


def test_run_never_overwrites_an_earlier_run(
    tmp_path: Path, settings: Any, eval_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_eval, "is_git_ignored", lambda _path: True)
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        _fake_webui(router, _chat_ok())
        run_eval.run(settings, eval_set, tmp_path, limit=1)
        run_eval.run(settings, eval_set, tmp_path, limit=1)
    names = sorted(p.name for p in tmp_path.glob("*.json") if p.name != "eval-set.yaml")
    assert len(names) == 2 and names[1].endswith("_2.json")


def test_run_refuses_a_folder_that_is_not_ignored(
    tmp_path: Path, settings: Any, eval_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_eval, "is_git_ignored", lambda _path: False)
    assert run_eval.run(settings, eval_set, tmp_path / "results") == 2
    assert not (tmp_path / "results").exists()


def test_run_stops_on_a_malformed_eval_set(
    tmp_path: Path, settings: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_eval, "is_git_ignored", lambda _path: True)
    bad = tmp_path / "bad.yaml"
    bad.write_text("questions: [{id: L01, category: other}]\n", encoding="utf-8")
    assert run_eval.run(settings, bad, tmp_path / "results") == 2


def test_summarise_counts_marks(
    tmp_path: Path, settings: Any, eval_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(run_eval, "is_git_ignored", lambda _path: True)
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        _fake_webui(router, _chat_ok())
        run_eval.run(settings, eval_set, tmp_path / "r")
    path = next((tmp_path / "r").glob("*.json"))
    results = json.loads(path.read_text())
    for record, mark in zip(results["records"], ["correct", "bogus", ""], strict=True):
        record["mark"] = mark
    path.write_text(json.dumps(results))
    assert run_eval.summarise(path) == 0
    summary = path.with_suffix(".md").read_text()
    assert "## Marks" in summary
    assert "| all | 1 | 0 | 0 | 0 | 1 | 1 |" in summary


def test_main_reports_missing_settings_by_name(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    for name in ("EVAL_API_KEY", "EVAL_KNOWLEDGE_ID", "EVAL_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setitem(run_eval.EvalSettings.model_config, "env_file", None)
    assert run_eval.main([]) == 2
    assert "EVAL_API_KEY" in caplog.text and "EVAL_MODEL" in caplog.text
