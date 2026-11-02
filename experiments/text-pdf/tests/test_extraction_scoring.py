"""Independent reference checks through pure scoring and saved CLI operations."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from soulkiller_text.extraction_cli import main
from soulkiller_text.extraction_display import render_score
from soulkiller_text.extraction_scoring import score_extraction
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.load_corpus import load_corpus
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.run_status import RunStatus
from soulkiller_text.run_store import create_run_store
from soulkiller_text.saved_run import run_saved_corpus
from soulkiller_text.saved_run_writer import manifest_payload
from soulkiller_text.text_annotation import TextAnnotation
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .manual_cli_fixtures import prepare_run, text_reference


@pytest.mark.parametrize(
    ("text", "recovered", "located", "location"),
    [
        ("x café", 1, 1, (None, 2, 6)),
        ("x café café", 1, 1, (None, 2, 6)),
        ("café", 1, 0, (None, 0, 4)),
        ("x cafe\u0301", 0, 0, None),
        ("x Café", 0, 0, None),
        ("café café", 1, 0, (None, 0, 4)),
        ("", 0, 0, None),
    ],
)
def test_exact_text_reference_distinguishes_recovery_from_location(
    text: str, recovered: int, located: int, location: tuple[None, int, int] | None
) -> None:
    """Unicode spelling, offsets and repeated quotes have independently fixed expectations."""
    # Arrange
    spec = text_reference()
    row = FixtureRun(spec, WorkerResult(WorkerOutcome.SUCCESS, spec.sha256, text))
    # Act
    report = score_extraction(RunStatus.COMPLETE, (spec,), (row,))
    # Assert
    assert report["expected_facts"] == 1
    assert report["recovered_facts"] == recovered
    assert report["correct_locations"] == located
    assert json.loads(json.dumps(report))["documents"][0]["facts"][0]["observed_location"] == (
        None if location is None else list(location)
    )


@pytest.mark.parametrize(
    ("pages", "outcome", "located", "location"),
    [
        ((PdfPage(1, "café"),), PdfWorkerOutcome.PARTIAL, 0, (1, 0, 4)),
        ((PdfPage(1, "café"), PdfPage(2, "Un café")), PdfWorkerOutcome.SUCCESS, 1, (2, 3, 7)),
        ((PdfPage(2, "ca"), PdfPage(3, "fé")), PdfWorkerOutcome.PARTIAL, 0, None),
    ],
)
def test_pdf_facts_keep_page_attribution_and_partial_outcomes(
    pages: tuple[PdfPage, ...],
    outcome: PdfWorkerOutcome,
    located: int,
    location: tuple[int, int, int] | None,
) -> None:
    """Wrong-page recovery differs from correct pages; facts never span page boundaries."""
    # Arrange
    spec = PdfCorpusFixture(
        "pdf-fr",
        "notes.pdf",
        "b" * 64,
        "pdf",
        "fr",
        "Invented",
        "Invented",
        "success",
        (PdfFactAnnotation(2, "café"),),
        3,
    )
    row = FixtureRun(spec, PdfWorkerResult(outcome, spec.sha256, pages, 3, ()))
    # Act
    report = score_extraction(RunStatus.COMPLETE, (spec,), (row,))
    # Assert
    assert report["expected_facts"] == 1
    assert report["recovered_facts"] == (location is not None)
    assert report["correct_locations"] == located
    assert json.loads(json.dumps(report))["documents"][0]["facts"][0]["observed_location"] == (
        None if location is None else list(location)
    )
    assert json.loads(json.dumps(report))["documents"][0]["observed_outcome"] == outcome.value


@pytest.mark.parametrize("state", ["missing", "unfinished", "failure"])
def test_unavailable_text_retains_reference_denominator(state: str) -> None:
    """Missing, unscheduled and failed observations cannot erase expected facts."""
    # Arrange
    spec = text_reference()
    row = None if state == "missing" else FixtureRun(spec)
    if state == "failure":
        row = FixtureRun(spec, WorkerResult(WorkerOutcome.TIMEOUT, spec.sha256, None))
    # Act
    report = score_extraction(None, (spec,), (row,))
    # Assert
    assert report["status"] == "incomplete"
    assert report["expected_facts"] == 1 and report["recovered_facts"] == 0
    assert report["outcome_matches"] == 0


def test_expected_error_is_an_outcome_match_without_a_fact_score() -> None:
    """An expected error agrees with the reference without fabricating recovered text."""
    # Arrange
    spec = replace(text_reference(), outcome="invalid_encoding", annotations=())
    row = FixtureRun(spec, WorkerResult(WorkerOutcome.INVALID_ENCODING, spec.sha256, None))
    # Act
    report = score_extraction(RunStatus.COMPLETE, (spec,), (row,))
    # Assert
    assert report["outcome_matches"] == 1 and report["expected_facts"] == 0
    assert report["unannotated_documents"] == 1
    assert "0/0" in render_score(report, as_json=False)


def test_reference_alignment_mismatch_is_not_silently_truncated() -> None:
    """A caller cannot drop a document from totals by passing fewer observations."""
    # Arrange
    # Act
    with pytest.raises(ValueError):
        score_extraction(None, (text_reference(),), ())
    # Assert: no truncated report was returned.


def test_score_cli_uses_saved_annotations_without_workers_or_current_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Connected inspection survives removed input files and leaves saved records untouched."""
    # Arrange
    calls = prepare_run(tmp_path, monkeypatch)
    run_saved_corpus(tmp_path, "corpus", "saved")
    for path in (tmp_path / "corpus").iterdir():
        path.unlink()
    output = tmp_path / ".soulkiller-local/evaluation/saved"
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["score", "--corpus", "corpus", "--run-id", "saved", "--json"])
    # Assert
    report = json.loads(capsys.readouterr().out)
    assert code == 0 and len(calls) == 3
    assert report["recovered_facts"] == report["correct_locations"] == 3
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


def test_incomplete_score_cli_keeps_missing_document_references(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Manifest-only progress keeps all expected facts while returning incomplete exit 1."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    fixtures = load_corpus(tmp_path, "corpus")
    with create_run_store(tmp_path, "corpus", "interrupted") as store:
        store.write_record("manifest", manifest_payload(fixtures))
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["score", "--corpus", "corpus", "--run-id", "interrupted"])
    # Assert
    output = capsys.readouterr().out
    assert code == 1 and "Run status: incomplete" in output
    assert "Exact quote recovery: 0/3" in output
    assert "observed unknown" in output


def test_score_display_escapes_terminal_controls() -> None:
    """Untrusted source quotes remain visible text rather than terminal instructions."""
    # Arrange
    spec = replace(text_reference(), annotations=(TextAnnotation(0, 1, "\x1b"),))
    row = FixtureRun(spec, WorkerResult(WorkerOutcome.SUCCESS, spec.sha256, "\x1b"))
    # Act
    output = render_score(score_extraction(RunStatus.COMPLETE, (spec,), (row,)), as_json=False)
    # Assert
    assert "\x1b" not in output
    assert "\\x1b" in output


def test_score_display_rejects_non_document_report() -> None:
    """Malformed internal report values produce a controlled failure rather than iteration."""
    # Arrange
    report = score_extraction(None, (), ())
    report["documents"] = None
    # Act
    with pytest.raises(ValueError, match="invalid_score_report"):
        render_score(report, as_json=False)
    # Assert: no malformed document was rendered.


def test_score_cli_reports_quality_mismatch_without_inventing_a_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A complete run can return a failed observed outcome while scoring still succeeds."""
    # Arrange
    from .corpus_run_fixtures import recording_workers

    prepare_run(tmp_path, monkeypatch)
    recording_workers(monkeypatch, outcomes=(WorkerOutcome.TIMEOUT,) * 3)
    run_saved_corpus(tmp_path, "corpus", "failed")
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["score", "--corpus", "corpus", "--run-id", "failed"])
    # Assert
    output = capsys.readouterr().out
    assert code == 0
    assert "Exact quote recovery: 0/3" in output
    assert "Expected outcome matches: 0/3" in output
    assert "observed timeout" in output


def test_score_cli_preserves_cancelled_status_exit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Cancelled runs keep completed evidence and cancelled exit 130 during scoring."""
    # Arrange
    prepare_run(tmp_path, monkeypatch, fault=KeyboardInterrupt())
    run_saved_corpus(tmp_path, "corpus", "cancelled")
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["score", "--corpus", "corpus", "--run-id", "cancelled", "--json"])
    # Assert
    report = json.loads(capsys.readouterr().out)
    assert code == 130 and report["status"] == "cancelled"
    assert report["recovered_facts"] == 1 and report["expected_facts"] == 3


def test_score_cli_unknown_id_does_not_create_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Inspection failures have no traceback or newly created run directory."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    # Act
    code = main(["score", "--corpus", "corpus", "--run-id", "unknown"])
    # Assert
    output = capsys.readouterr()
    assert code == 1 and "Extraction failed:" in output.err
    assert "Traceback" not in output.err
    assert not (tmp_path / ".soulkiller-local/evaluation/unknown").exists()
