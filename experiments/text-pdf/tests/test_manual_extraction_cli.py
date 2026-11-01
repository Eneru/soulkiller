"""Observable commands, safe text and actual offline module execution."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from soulkiller_text.extraction_cli import main
from soulkiller_text.extraction_display import render_saved, safe_display
from soulkiller_text.saved_json import decode_saved

from .corpus_run_fixtures import mixed_execution_corpus
from .manual_cli_fixtures import prepare_run
from .pdf_worker_fixtures import externally_offline


def test_cli_run_prints_readable_results_and_saved_location(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The primary user command exposes source references, text and the saved folder."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["run", "--corpus", "corpus", "--run-id", "example"])
    # Assert
    output = capsys.readouterr()
    assert code == 0
    assert "Run status: complete" in output.out
    assert "z-last.txt" in output.out and "abc" in output.out
    assert ".soulkiller-local/evaluation/example/" in output.out


def test_show_json_is_parseable_and_does_not_rerun_workers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Inspection returns exact evidence without launching more workers."""
    # Arrange
    calls = prepare_run(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    main(["run", "--corpus", "corpus", "--run-id", "example"])
    capsys.readouterr()
    # Act
    code = main(["show", "--corpus", "corpus", "--run-id", "example", "--json"])
    # Assert
    document = json.loads(capsys.readouterr().out)
    assert code == 0 and len(calls) == 3
    assert document["fixtures"][0]["result"]["text"] == "abc"


def test_connected_cli_explains_offline_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An environment mistake produces actionable guidance without a traceback."""
    # Arrange
    from importlib import import_module

    module = import_module("soulkiller_text.saved_run")
    monkeypatch.setattr(module, "has_offline_topology", lambda: False)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["run", "--run-id", "example"])
    # Assert
    output = capsys.readouterr()
    assert code == 1 and "--network none" in output.err
    assert "Traceback" not in output.err


@pytest.mark.parametrize(
    "payload", [b"[]", b'{"x":NaN}', b'{"x":1.5}', b'{"x":1,"x":2}', b"\xff", b"[" * 2000]
)
def test_saved_json_rejects_invalid_metadata(payload: bytes) -> None:
    """Metadata parser refuses ambiguous or malformed bounded wire."""
    # Arrange
    # Act
    with pytest.raises(ValueError):
        decode_saved(payload)
    # Assert: no value was accepted.


def test_plain_display_escapes_controls_but_preserves_readable_unicode() -> None:
    """Terminal escape/bidi controls cannot become executable display instructions."""
    # Arrange
    text = "é\n\x1b[31m\u202e"
    # Act
    result = safe_display(text)
    # Assert
    assert result == "é\n\\u001b[31m\\u202e"


def test_incomplete_display_names_unknown_state() -> None:
    """A missing record stays explicitly unavailable rather than becoming success."""
    # Arrange
    # Act
    output = render_saved(None, (None,), as_json=False)
    # Assert
    assert "incomplete" in output and "unknown" in output


def test_actual_module_cli_respects_external_offline_boundary(tmp_path: Path) -> None:
    """Fresh CLI processes prove actual mixed extraction offline and refusal when connected."""
    # Arrange
    mixed_execution_corpus(tmp_path)
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    command = [
        sys.executable,
        "-m",
        "soulkiller_text",
        "run",
        "--corpus",
        "corpus",
        "--run-id",
        "real",
    ]
    # Act
    result = subprocess.run(
        command, cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30
    )
    # Assert
    if externally_offline():
        assert result.returncode == 0, result.stderr
        assert "[Page 2]" in result.stdout and "lampe bleue" in result.stdout
        assert "invalid_encoding" in result.stdout and "malformed_input" in result.stdout
    else:
        assert result.returncode == 1
        assert "--network none" in result.stderr
        assert not (tmp_path / ".soulkiller-local").exists()


def test_default_example_contains_verified_bilingual_text_and_pdf() -> None:
    """The actual shipped demo must exercise PDFs as well as text and an expected error."""
    # Arrange
    from soulkiller_text.load_corpus import load_corpus
    from soulkiller_text.manual_cli_constants import DEFAULT_CORPUS

    workspace = Path(__file__).resolve().parents[3]
    # Act
    fixtures = load_corpus(workspace, DEFAULT_CORPUS)
    # Assert
    assert len(fixtures) == 5
    assert sum(f.specification.format == "pdf" for f in fixtures) == 2
    assert {f.specification.language for f in fixtures} == {"fr", "en"}
    assert any(f.specification.outcome == "invalid_encoding" for f in fixtures)
