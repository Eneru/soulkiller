"""Ordered scheduling retains independent snapshots, outcomes and page findings."""

from dataclasses import FrozenInstanceError
from importlib import import_module
from pathlib import Path

import pytest

from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.run_corpus import run_corpus
from soulkiller_text.run_status import RunStatus
from soulkiller_text.synthetic_pdf import build_text_pdf
from soulkiller_text.worker_execution import WorkerExecution
from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .corpus_helpers import fixture_document
from .corpus_run_fixtures import (
    mixed_execution_corpus,
    ordered_text_corpus,
    permit_scheduling,
    recording_workers,
)
from .pdf_corpus_fixtures import pdf_document, write_evaluation_corpus
from .pdf_worker_fixtures import externally_offline


def test_manifest_order_preserves_labels_revisions_and_measured_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch, counts=(4, 6, 3))
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert [row.specification.fixture_id for row in result.fixtures] == [
        "z-last",
        "a-first",
        "m-middle",
    ]
    assert [row.output_bytes for row in result.fixtures] == [4, 6, 3]
    assert result.output_bytes == 13
    assert len(calls) == 3
    assert all(row.specification.author_label == "Synthetic author" for row in result.fixtures)
    assert all(
        row.result is not None and row.result.source_sha256 == row.specification.sha256
        for row in result.fixtures
    )
    assert all(row.unfinished_reason is None for row in result.fixtures)


def test_later_stale_revision_prevents_even_the_first_worker_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    corpus = ordered_text_corpus(tmp_path)
    (corpus / "a-first.txt").write_bytes(b"changed after reference declaration")
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch)
    # Act
    with pytest.raises(CorpusError) as failure:
        run_corpus(tmp_path, "corpus")
    # Assert
    assert failure.value.category == "source_mismatch"
    assert calls == []


def test_later_snapshot_is_not_reread_when_worker_changes_disk_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    corpus = ordered_text_corpus(tmp_path, 2)
    permit_scheduling(monkeypatch)

    def replace_later_source() -> None:
        (corpus / "a-first.txt").write_bytes(b"new revision")

    calls = recording_workers(monkeypatch, on_call=replace_later_source)
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert [call[1] for call in calls] == [b"abc", b"abc"]
    assert (corpus / "a-first.txt").read_bytes() == b"new revision"


@pytest.mark.parametrize(
    "outcome",
    [
        WorkerOutcome.INVALID_ENCODING,
        WorkerOutcome.PROTOCOL_ERROR,
        WorkerOutcome.TIMEOUT,
        WorkerOutcome.RESOURCE_LIMIT,
        WorkerOutcome.OUTPUT_LIMIT,
        WorkerOutcome.CANDIDATE_FAILURE,
    ],
)
def test_per_file_failure_remains_visible_and_does_not_prevent_next_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, outcome: WorkerOutcome
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 2)
    permit_scheduling(monkeypatch)
    calls = recording_workers(
        monkeypatch, counts=(11, 3), outcomes=(outcome, WorkerOutcome.SUCCESS)
    )
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert result.fixtures[0].result is not None
    assert result.fixtures[0].result.outcome is outcome
    assert result.fixtures[1].result is not None
    assert result.fixtures[1].result.outcome is WorkerOutcome.SUCCESS
    assert result.output_bytes == 14
    assert len(calls) == 2


def test_declared_pdf_pages_are_worker_ceiling_and_expectations_are_not_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    source = build_text_pdf(("This physical page has an independent fact.",))
    specification = pdf_document("declared-pdf", "sample.pdf", source)
    specification.update({"page_count": 3, "outcome": "no_text", "annotations": []})
    write_evaluation_corpus(tmp_path, [specification], {"sample.pdf": source})
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch)
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert calls[0][0] == "pdf"
    assert calls[0][3] == 3
    row = result.fixtures[0]
    assert row.specification.outcome == "no_text"
    assert isinstance(row.result, PdfWorkerResult)
    assert row.result.outcome is PdfWorkerOutcome.SUCCESS
    assert row.result.total_pages == 1
    assert row.result.pages[0].text == "Independent worker value"


@pytest.mark.parametrize("field", ["status", "fixtures", "output_bytes"])
def test_completed_run_result_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 1)
    permit_scheduling(monkeypatch)
    recording_workers(monkeypatch)
    result = run_corpus(tmp_path, "corpus")
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(result, field, None)


@pytest.mark.parametrize("field", ["specification", "result", "output_bytes", "unfinished_reason"])
def test_completed_fixture_row_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 1)
    permit_scheduling(monkeypatch)
    recording_workers(monkeypatch)
    row = run_corpus(tmp_path, "corpus").fixtures[0]
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(row, field, None)


def test_real_bilingual_mixed_corpus_refuses_connected_or_extracts_offline(tmp_path: Path) -> None:
    # Arrange
    mixed_execution_corpus(tmp_path)
    offline = externally_offline()
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert len(result.fixtures) == 5
    if not offline:
        assert result.status is RunStatus.UNSUPPORTED_ENVIRONMENT
        assert result.output_bytes == 0
        assert all(
            row.result is None and row.unfinished_reason is RunStatus.UNSUPPORTED_ENVIRONMENT
            for row in result.fixtures
        )
        return
    assert result.status is RunStatus.COMPLETE
    assert [row.result.outcome for row in result.fixtures if row.result is not None] == [
        WorkerOutcome.INVALID_ENCODING,
        WorkerOutcome.SUCCESS,
        PdfWorkerOutcome.SUCCESS,
        PdfWorkerOutcome.MALFORMED_INPUT,
        PdfWorkerOutcome.SUCCESS,
    ]
    text = result.fixtures[1].result
    french = result.fixtures[2].result
    english = result.fixtures[4].result
    assert isinstance(text, WorkerResult) and text.text == "abc"
    assert isinstance(french, PdfWorkerResult) and french.total_pages == 2
    assert (
        french.pages[0].page_number == 1 and "Inez garde une lampe bleue." in french.pages[0].text
    )
    assert isinstance(english, PdfWorkerResult) and english.total_pages == 1
    assert "Corin collects paper stars." in english.pages[0].text
    assert result.output_bytes is not None and result.output_bytes > 0


def test_real_underdeclared_pdf_retains_page_limit_and_later_text(tmp_path: Path) -> None:
    # Arrange
    source = build_text_pdf(("First invented page.", "Second invented page."))
    pdf = pdf_document("underdeclared", "sample.pdf", source)
    pdf.update({"page_count": 1, "annotations": []})
    write_evaluation_corpus(
        tmp_path,
        [pdf, fixture_document("later", "later.txt")],
        {"sample.pdf": source, "later.txt": b"abc"},
    )
    offline = externally_offline()
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    if not offline:
        assert result.status is RunStatus.UNSUPPORTED_ENVIRONMENT
        assert all(row.result is None for row in result.fixtures)
        return
    assert result.status is RunStatus.COMPLETE
    first = result.fixtures[0].result
    assert isinstance(first, PdfWorkerResult)
    assert first.outcome is PdfWorkerOutcome.PAGE_LIMIT
    assert first.total_pages == 2 and first.pages == ()
    assert result.fixtures[1].result is not None
    assert result.fixtures[1].result.outcome is WorkerOutcome.SUCCESS


def test_partial_pdf_pages_and_missing_numbers_remain_visible_without_scoring(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    source = build_text_pdf(("First invented page.", "Second invented page."))
    document = pdf_document("partial", "partial.pdf", source)
    document["annotations"] = []
    write_evaluation_corpus(tmp_path, [document], {"partial.pdf": source})
    permit_scheduling(monkeypatch)
    observed = PdfWorkerResult(
        PdfWorkerOutcome.PARTIAL,
        str(document["sha256"]),
        (PdfPage(1, "Recovered independent fact."),),
        2,
        (2,),
    )

    def partial_worker(
        source: bytes, limits: WorkerLimits, max_pages: int
    ) -> WorkerExecution[PdfWorkerResult]:
        return WorkerExecution(observed, 17)

    monkeypatch.setattr(
        import_module("soulkiller_text.corpus_runner"), "run_observed_pdf_worker", partial_worker
    )
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.COMPLETE
    row = result.fixtures[0]
    assert row.result is observed
    assert isinstance(row.result, PdfWorkerResult)
    assert row.result.outcome is PdfWorkerOutcome.PARTIAL
    assert row.result.pages == (PdfPage(1, "Recovered independent fact."),)
    assert row.result.missing_pages == (2,) and row.output_bytes == 17
    assert row.specification.outcome == "success"


def test_pdf_unavailable_worker_guard_stops_later_txt_without_hiding_pdf_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    source = build_text_pdf(("One invented page.",))
    document = pdf_document("unavailable", "sample.pdf", source)
    document.update({"page_count": 1, "annotations": []})
    write_evaluation_corpus(
        tmp_path,
        [document, fixture_document("later", "later.txt")],
        {"sample.pdf": source, "later.txt": b"abc"},
    )
    permit_scheduling(monkeypatch)
    calls = recording_workers(
        monkeypatch, counts=(5,), outcomes=(PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT,)
    )
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.UNSUPPORTED_ENVIRONMENT
    assert len(calls) == 1 and calls[0][0] == "pdf"
    assert result.fixtures[0].result is not None
    assert result.fixtures[0].result.outcome is PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
    assert result.output_bytes == 5
    assert result.fixtures[1].result is None and result.fixtures[1].output_bytes == 0
    assert result.fixtures[1].unfinished_reason is RunStatus.UNSUPPORTED_ENVIRONMENT
