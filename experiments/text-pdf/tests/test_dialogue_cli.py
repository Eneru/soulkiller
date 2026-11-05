"""Read-only manual ask behavior, explicit scripted choices and safe CLI failures."""

import json
from pathlib import Path

import pytest

from soulkiller_text.dialogue_constants import DIALOGUE_CORPUS
from soulkiller_text.extraction_cli import main

from .dialogue_fixtures import saved_dialogue


@pytest.mark.parametrize(
    ("case", "query", "language", "status", "source"),
    [
        ("lamp", "lampe bleue", "fr", "answer", "inez-fr"),
        ("paper-stars", "paper stars", "en", "answer", "inez-en"),
        ("conflict", "lampe", "fr", "conflict", "inez-fr"),
        ("third-party", "glass marbles", "en", "answer", "shared-letter"),
        ("uncertain", "Archived instruction", "en", "uncertain", "archived-instruction"),
    ],
)
def test_explicit_demo_reports_answers_and_locally_resolved_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
    query: str,
    language: str,
    status: str,
    source: str,
) -> None:
    """Each script exercises a distinct approved scenario without reading original files."""
    # Arrange
    saved_dialogue(tmp_path)
    for path in (tmp_path / DIALOGUE_CORPUS).iterdir():
        path.unlink()
    folder = tmp_path / ".soulkiller-local/evaluation/example"
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(
        [
            "ask",
            "--run-id",
            "example",
            "--profile",
            "inez",
            "--question",
            "Synthetic question?",
            "--evidence-query",
            query,
            "--language",
            language,
            "--demo-case",
            case,
            "--json",
        ]
    )
    # Assert
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert code == 0 and report["backend"] == "scripted_demo"
    assert report["status"] == status and report["sources"][0]["fixture_id"] == source
    assert "4 eligible documents" in output.err
    assert {p.name: p.read_bytes() for p in folder.iterdir()} == before


def test_readable_demo_separates_scripted_text_from_exact_pdf_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The operator can distinguish demonstration wording from actual retained source text."""
    # Arrange
    saved_dialogue(tmp_path)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(
        [
            "ask",
            "--run-id",
            "example",
            "--profile",
            "inez",
            "--question",
            "Quelle couleur ?",
            "--evidence-query",
            "lampe",
            "--language",
            "fr",
            "--demo-case",
            "conflict",
        ]
    )
    # Assert
    output = capsys.readouterr().out
    assert code == 0 and "Scripted demo only" in output
    assert "Response text:" in output and "Exact local sources" in output
    assert "PDF page 1" in output and "PDF page 2" in output
    assert "Je garde une lampe bleue." in output and "Je garde une lampe rouge." in output


def test_invalid_question_is_usage_failure_before_store_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A blank input cannot trigger extraction, a model or a file lookup."""
    # Arrange
    monkeypatch.chdir(tmp_path)
    # Act
    with pytest.raises(SystemExit) as error:
        main(
            [
                "ask",
                "--run-id",
                "missing",
                "--profile",
                "inez",
                "--question",
                " ",
                "--evidence-query",
                "lampe",
                "--language",
                "fr",
                "--demo-case",
                "lamp",
            ]
        )
    # Assert
    assert error.value.code == 2
    assert "invalid_question" in capsys.readouterr().err
    assert not (tmp_path / ".soulkiller-local").exists()


def test_dialogue_failure_is_visible_without_an_answer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Refuse an evidence-limited run with a fixed diagnostic and no partial answer."""
    # Arrange
    saved_dialogue(tmp_path)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(
        [
            "ask",
            "--run-id",
            "example",
            "--profile",
            "inez",
            "--question",
            "Question?",
            "--evidence-query",
            "e",
            "--language",
            "fr",
            "--demo-case",
            "lamp",
        ]
    )
    # Assert
    output = capsys.readouterr()
    assert code == 1 and output.out == ""
    assert "Dialogue failed: truncated_persona_evidence" in output.err
