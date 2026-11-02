"""Exact saved-reference checks, separate from semantic quality or ranking."""

from dataclasses import asdict

from .corpus_fixture import CorpusFixture
from .fact_score import FactScore, Location
from .fixture_run import FixtureRun
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_fact_annotation import PdfFactAnnotation
from .pdf_worker_result import PdfWorkerResult
from .run_status import RunStatus
from .text_annotation import TextAnnotation
from .worker_result import WorkerResult


def _text_fact(annotation: TextAnnotation, row: FixtureRun | None) -> FactScore:
    """Prefer the exact annotated range; otherwise expose the first literal match."""
    result = None if row is None else row.result
    text = result.text if isinstance(result, WorkerResult) else None
    expected: Location = (None, annotation.start, annotation.end)
    matched = text is not None and text[annotation.start : annotation.end] == annotation.quote
    start = annotation.start if matched else (-1 if text is None else text.find(annotation.quote))
    observed = None if start < 0 else (None, start, start + len(annotation.quote))
    return FactScore(annotation.quote, expected, observed, matched)


def _pdf_fact(annotation: PdfFactAnnotation, row: FixtureRun | None) -> FactScore:
    """Search individual saved pages, preferring the expected page without joining text."""
    result = None if row is None else row.result
    pages = result.pages if isinstance(result, PdfWorkerResult) else ()
    ordered = sorted(pages, key=lambda page: page.page_number != annotation.page_number)
    observed: Location | None = None
    for page in ordered:
        start = page.text.find(annotation.quote)
        if start >= 0:
            observed = (page.page_number, start, start + len(annotation.quote))
            break
    matched = observed is not None and observed[0] == annotation.page_number
    return FactScore(annotation.quote, (annotation.page_number, None, None), observed, matched)


def _facts(
    specification: CorpusFixture | PdfCorpusFixture, row: FixtureRun | None
) -> tuple[FactScore, ...]:
    """Check only independent saved annotations, retaining references for missing rows."""
    if isinstance(specification, CorpusFixture):
        return tuple(_text_fact(annotation, row) for annotation in specification.annotations)
    return tuple(_pdf_fact(annotation, row) for annotation in specification.annotations)


def _observed_outcome(row: FixtureRun | None) -> str:
    """Distinguish unavailable saved rows from observed failures and unscheduled work."""
    if row is None:
        return "unknown"
    if row.result is None:
        return "unfinished"
    return row.result.outcome.value


def score_extraction(
    status: RunStatus | None,
    specifications: tuple[CorpusFixture | PdfCorpusFixture, ...],
    rows: tuple[FixtureRun | None, ...],
) -> dict[str, object]:
    """Summarize validated saved evidence; mismatches are observations, not gate decisions.

    The reader supplies aligned metadata/rows. Reject length mismatches rather
    than dropping denominators. Every quote stays expected even without evidence.
    """
    documents: list[dict[str, object]] = []
    expected = recovered = located = outcome_matches = unannotated = 0
    for specification, row in zip(specifications, rows, strict=True):
        facts = _facts(specification, row)
        observed = _observed_outcome(row)
        agreement = observed == specification.outcome
        expected += len(facts)
        recovered += sum(fact.observed_location is not None for fact in facts)
        located += sum(fact.location_matched for fact in facts)
        outcome_matches += agreement
        unannotated += not facts
        documents.append(
            {
                "fixture_id": specification.fixture_id,
                "source_sha256": specification.sha256,
                "expected_outcome": specification.outcome,
                "observed_outcome": observed,
                "outcome_matched": agreement,
                "facts": [asdict(fact) for fact in facts],
            }
        )
    return {
        "status": "incomplete" if status is None else status.value,
        "matching": "exact Unicode code points; no normalization",
        "expected_facts": expected,
        "recovered_facts": recovered,
        "correct_locations": located,
        "outcome_matches": outcome_matches,
        "expected_outcomes": len(specifications),
        "unannotated_documents": unannotated,
        "documents": documents,
    }
