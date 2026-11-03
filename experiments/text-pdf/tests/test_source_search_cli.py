"""Observable saved-source search with strict persistence and actual module execution."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from soulkiller_text.extraction_cli import main
from soulkiller_text.saved_run import run_saved_corpus
from soulkiller_text.search_display import render_search
from soulkiller_text.source_search import search_evidence

from .manual_cli_fixtures import prepare_run
from .source_search_fixtures import save_partial_search_run, text_row


def test_search_reopens_saved_evidence_without_inputs_workers_or_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Read-only inspection preserves saved bytes even after original files/manifest disappear."""
    # Arrange
    calls = prepare_run(tmp_path, monkeypatch)
    run_saved_corpus(tmp_path, "corpus", "saved")
    for path in (tmp_path / "corpus").iterdir():
        path.unlink()
    folder = tmp_path / ".soulkiller-local/evaluation/saved"
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["search", "--corpus", "corpus", "--run-id", "saved", "--query", "abc", "--json"])
    # Assert
    report = json.loads(capsys.readouterr().out)
    assert code == 0 and len(calls) == 3
    assert [hit["fixture_id"] for hit in report["matches"]] == ["z-last", "a-first", "m-middle"]
    assert report["matches"][0]["quote"] == "abc"
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before


def test_partial_search_prints_hit_with_incomplete_status_and_coverage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A partial page hit never hides unavailable document rows or a missing final summary."""
    # Arrange
    save_partial_search_run(tmp_path)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["search", "--corpus", "corpus", "--run-id", "partial", "--query", "lampe bleue"])
    # Assert
    output = capsys.readouterr().out
    assert code == 1 and "Run status: incomplete" in output
    assert "PDF page 1" in output and "lampe bleue" in output
    assert "missing pages: 2" in output and "unknown" in output
    assert "partial" in output and "no relevance or truth ranking" in output


def test_corrupt_later_row_blocks_results_even_when_an_earlier_hit_fills_limit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """All saved rows are validated before returning trusted search matches."""
    # Arrange
    save_partial_search_run(tmp_path, corrupt_later=True)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(
        [
            "search",
            "--corpus",
            "corpus",
            "--run-id",
            "partial",
            "--query",
            "lampe bleue",
            "--limit",
            "1",
        ]
    )
    # Assert
    output = capsys.readouterr()
    assert code == 1 and output.out == ""
    assert "Extraction failed:" in output.err and "Traceback" not in output.err


def test_search_preserves_cancelled_saved_status_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A previous cancellation keeps usable evidence and exit 130 during later search."""
    # Arrange
    prepare_run(tmp_path, monkeypatch, fault=KeyboardInterrupt())
    run_saved_corpus(tmp_path, "corpus", "cancelled")
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(
        [
            "search",
            "--corpus",
            "corpus",
            "--run-id",
            "cancelled",
            "--query",
            "abc",
            "--json",
        ]
    )
    # Assert
    report = json.loads(capsys.readouterr().out)
    assert code == 130 and report["status"] == "cancelled"
    assert len(report["matches"]) == 1
    assert report["coverage"][1]["unfinished_reason"] == "cancelled"


def test_no_match_in_complete_run_is_a_successful_search(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No literal evidence is a visible search observation, not an invented answer or error."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    run_saved_corpus(tmp_path, "corpus", "saved")
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["search", "--corpus", "corpus", "--run-id", "saved", "--query", "absent"])
    # Assert
    output = capsys.readouterr().out
    assert code == 0 and "No matching passage was found" in output
    assert "Run status: complete" in output


@pytest.mark.parametrize(
    "options",
    [
        ["--query", ""],
        ["--query", " \n\t"],
        ["--query", "x" * 201],
        ["--query", "x", "--limit", "0"],
        ["--query", "x", "--limit", "21"],
        ["--query", "x", "--limit", "bad"],
        [],
    ],
)
def test_invalid_search_arguments_fail_before_saved_store_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    options: list[str],
) -> None:
    """Usage validation precedes any attempt to open the nonexistent run or create output."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    # Act
    with pytest.raises(SystemExit) as failure:
        main(["search", "--run-id", "nonexistent", *options])
    # Assert
    assert failure.value.code == 2
    output = capsys.readouterr()
    assert output.out == "" and "error:" in output.err
    assert "Extraction failed:" not in output.err
    assert not (tmp_path / ".soulkiller-local").exists()


def test_unknown_saved_run_returns_controlled_failure_without_creating_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A valid query does not turn search into implicit ingestion or store creation."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["search", "--corpus", "corpus", "--run-id", "missing", "--query", "abc"])
    # Assert
    output = capsys.readouterr()
    assert code == 1 and "Extraction failed:" in output.err
    assert not (tmp_path / ".soulkiller-local/evaluation/missing").exists()


def test_actual_module_search_requires_no_offline_worker_topology(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A fresh process reads existing evidence with no run/extraction call or source files."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    run_saved_corpus(tmp_path, "corpus", "saved")
    for path in (tmp_path / "corpus").iterdir():
        path.unlink()
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    # Act
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "soulkiller_text",
            "search",
            "--corpus",
            "corpus",
            "--run-id",
            "saved",
            "--query",
            "abc",
            "--limit",
            "1",
            "--json",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
    )
    # Assert
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert len(report["matches"]) == 1 and report["more_matches"]
    assert report["matches"][0]["quote"] == "abc"
    assert result.stderr == ""


def test_terminal_controls_are_escaped_but_json_retains_exact_evidence() -> None:
    """Neither an imported escape sequence nor bidi characters can execute as terminal controls."""
    # Arrange
    text = "café\x1b[31m\u202e"
    row = text_row(text)
    report = search_evidence(None, (row.specification,), (row,), "café")
    # Act
    readable = render_search(report, as_json=False)
    encoded = render_search(report, as_json=True)
    # Assert
    assert "\x1b" not in readable and "\u202e" not in readable
    assert "\\u001b" in readable and "\\u202e" in readable
    assert json.loads(encoded)["matches"][0]["excerpt"] == text
