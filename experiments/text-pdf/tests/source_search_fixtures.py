"""Independent saved observations for literal source-search scenarios."""

import hashlib
from pathlib import Path

from soulkiller_text.corpus_fixture import CorpusFixture
from soulkiller_text.fixture_record import encode_fixture_record
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.load_corpus import load_corpus
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.run_store import create_run_store
from soulkiller_text.saved_run_writer import manifest_payload
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult


def text_row(text: str, fixture_id: str = "z-text") -> FixtureRun:
    """Build an invented TXT observation with independent metadata and no reference facts."""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    spec = CorpusFixture(
        fixture_id,
        f"{fixture_id}.txt",
        digest,
        "txt",
        "fr",
        "Author label",
        "Subject label",
        "success",
        (),
    )
    return FixtureRun(spec, WorkerResult(WorkerOutcome.SUCCESS, digest, text))


def pdf_row(
    pages: tuple[PdfPage, ...],
    *,
    outcome: PdfWorkerOutcome = PdfWorkerOutcome.SUCCESS,
    total_pages: int | None = 2,
    missing_pages: tuple[int, ...] = (),
) -> FixtureRun:
    """Keep expected PDF facts distinct from independently declared candidate page text."""
    spec = PdfCorpusFixture(
        "a-pdf",
        "a-pdf.pdf",
        "b" * 64,
        "pdf",
        "en",
        "PDF author label",
        "PDF subject label",
        "success",
        (PdfFactAnnotation(2, "reference-only"),),
        2,
    )
    result = PdfWorkerResult(outcome, spec.sha256, pages, total_pages, missing_pages)
    return FixtureRun(spec, result)


def save_partial_search_run(workspace: Path, *, corrupt_later: bool = False) -> None:
    """Persist one real metadata-bound partial PDF row amid unavailable rows, without workers."""
    from .corpus_run_fixtures import mixed_execution_corpus

    mixed_execution_corpus(workspace)
    fixtures = load_corpus(workspace, "corpus")
    spec = fixtures[2].specification
    result = PdfWorkerResult(
        PdfWorkerOutcome.PARTIAL,
        spec.sha256,
        (PdfPage(1, "Inez garde une lampe bleue."),),
        2,
        (2,),
    )
    with create_run_store(workspace, "corpus", "partial") as store:
        store.write_record("manifest", manifest_payload(fixtures))
        store.write_record("fixture-003", encode_fixture_record(FixtureRun(spec, result, 1)))
        if corrupt_later:
            store.write_record("fixture-005", b"{}")
