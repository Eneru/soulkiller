"""Read-only literal search over already validated saved extraction evidence."""

from collections.abc import Iterator
from itertools import islice

from .corpus_fixture import CorpusFixture
from .fixture_run import FixtureRun
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_worker_result import PdfWorkerResult
from .run_status import RunStatus
from .search_constants import (
    CONTEXT_CODE_POINTS,
    DEFAULT_SEARCH_LIMIT,
    MAX_QUERY_CODE_POINTS,
    MAX_SEARCH_LIMIT,
    UNFINISHED_OUTCOME,
    UNKNOWN_OUTCOME,
)
from .search_coverage import SearchCoverage
from .search_report import SearchReport
from .source_match import SourceMatch
from .worker_outcome import WorkerOutcome
from .worker_result import WorkerResult


def validate_search(query: str, limit: int) -> None:
    """Reject invalid bounds without touching saved evidence or echoing query contents."""
    if (
        not isinstance(query, str)
        or not 1 <= len(query) <= MAX_QUERY_CODE_POINTS
        or query.isspace()
    ):
        raise ValueError(
            f"query must contain 1..{MAX_QUERY_CODE_POINTS} code points and nonblank text"
        )
    if type(limit) is not int or not 1 <= limit <= MAX_SEARCH_LIMIT:
        raise ValueError(f"limit must be an integer in 1..{MAX_SEARCH_LIMIT}")


def _units(row: FixtureRun | None) -> tuple[tuple[int | None, str], ...]:
    """Yield only retained candidate text, keeping physical PDF pages separate and ordered."""
    result = None if row is None else row.result
    if isinstance(result, PdfWorkerResult):
        return tuple(
            (p.page_number, p.text) for p in sorted(result.pages, key=lambda p: p.page_number)
        )
    if isinstance(result, WorkerResult) and result.outcome is WorkerOutcome.SUCCESS:
        return ((None, result.text),) if result.text is not None else ()
    return ()


def _coverage(
    specification: CorpusFixture | PdfCorpusFixture, row: FixtureRun | None
) -> SearchCoverage:
    """Expose failed/unknown coverage independently of matches and final scheduling status."""
    result = None if row is None else row.result
    outcome = UNKNOWN_OUTCOME if row is None else UNFINISHED_OUTCOME
    if result is not None:
        outcome = result.outcome.value
    pdf = result if isinstance(result, PdfWorkerResult) else None
    return SearchCoverage(
        fixture_id=specification.fixture_id,
        path=specification.path,
        format=specification.format,
        outcome=outcome,
        unfinished_reason=None if row is None else row.unfinished_reason,
        text_available=any(text for _page, text in _units(row)),
        retained_pages=None if pdf is None else tuple(p.page_number for p in pdf.pages),
        total_pages=None if pdf is None else pdf.total_pages,
        missing_pages=None if pdf is None or pdf.total_pages is None else pdf.missing_pages,
    )


def _unit_matches(
    specification: CorpusFixture | PdfCorpusFixture, page: int | None, text: str, query: str
) -> Iterator[SourceMatch]:
    """Enumerate non-overlapping literal spans and clipped context without altering code points."""
    cursor = 0
    while (start := text.find(query, cursor)) >= 0:
        end = start + len(query)
        excerpt_start = max(0, start - CONTEXT_CODE_POINTS)
        excerpt_end = min(len(text), end + CONTEXT_CODE_POINTS)
        yield SourceMatch(
            fixture_id=specification.fixture_id,
            path=specification.path,
            source_sha256=specification.sha256,
            format=specification.format,
            language=specification.language,
            author_label=specification.author_label,
            subject_label=specification.subject_label,
            page_number=page,
            match_start=start,
            match_end=end,
            excerpt_start=excerpt_start,
            excerpt_end=excerpt_end,
            quote=text[start:end],
            excerpt=text[excerpt_start:excerpt_end],
        )
        cursor = end


def _matches(
    specifications: tuple[CorpusFixture | PdfCorpusFixture, ...],
    rows: tuple[FixtureRun | None, ...],
    query: str,
) -> Iterator[SourceMatch]:
    """Preserve manifest/page/start order; reference annotations never participate in matching."""
    for specification, row in zip(specifications, rows, strict=True):
        for page, text in _units(row):
            yield from _unit_matches(specification, page, text, query)


def search_evidence(
    status: RunStatus | None,
    specifications: tuple[CorpusFixture | PdfCorpusFixture, ...],
    rows: tuple[FixtureRun | None, ...],
    query: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> SearchReport:
    """Search aligned validated saved rows; collect one extra hit solely to disclose truncation.

    Coverage exhausts the metadata/row alignment before matching, so a limit
    cannot hide missing specifications. The saved reader, not these value
    containers, owns integrity/type validation. No source I/O or writes occur.
    """
    validate_search(query, limit)
    coverage = tuple(_coverage(spec, row) for spec, row in zip(specifications, rows, strict=True))
    found = tuple(islice(_matches(specifications, rows, query), limit + 1))
    return SearchReport(
        status="incomplete" if status is None else status.value,
        query=query,
        limit=limit,
        matches=found[:limit],
        more_matches=len(found) > limit,
        coverage=coverage,
    )
