"""Literal matching, independent source references and visible extraction coverage."""

from dataclasses import replace
from typing import cast

import pytest

from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.run_status import RunStatus
from soulkiller_text.source_search import search_evidence
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .source_search_fixtures import pdf_row, text_row


def test_unicode_match_and_context_resolve_exactly_in_saved_text() -> None:
    """CRLF and accented characters use code points without changing the saved evidence."""
    # Arrange
    text = "é\r\ncafé\n"
    row = text_row(text)
    # Act
    report = search_evidence(RunStatus.COMPLETE, (row.specification,), (row,), "café")
    # Assert
    (hit,) = report.matches
    assert (hit.match_start, hit.match_end) == (3, 7)
    assert text[hit.match_start : hit.match_end] == hit.quote == "café"
    assert text[hit.excerpt_start : hit.excerpt_end] == hit.excerpt == text
    assert hit.source_sha256 == row.specification.sha256
    assert (hit.path, hit.language, hit.author_label, hit.subject_label) == (
        "z-text.txt",
        "fr",
        "Author label",
        "Subject label",
    )
    assert hit.page_number is None


def test_context_is_clipped_to_eighty_code_points_on_each_side() -> None:
    """A long passage returns only the approved resolving context, not the whole document."""
    # Arrange
    text = "α" * 100 + "needle" + "β" * 100
    row = text_row(text)
    # Act
    report = search_evidence(None, (row.specification,), (row,), "needle")
    # Assert
    (hit,) = report.matches
    assert (hit.match_start, hit.match_end) == (100, 106)
    assert (hit.excerpt_start, hit.excerpt_end) == (20, 186)
    assert hit.excerpt == "α" * 80 + "needle" + "β" * 80


def test_maximum_query_and_limit_are_accepted_with_bounded_excerpt() -> None:
    """The approved inclusive query/limit boundaries preserve exact match and context."""
    # Arrange
    query = "é" * 200
    row = text_row("a" * 100 + query + "b" * 100)
    # Act
    report = search_evidence(None, (row.specification,), (row,), query, 20)
    # Assert
    (hit,) = report.matches
    assert hit.quote == query and len(hit.excerpt) == 360
    assert report.limit == 20 and not report.more_matches


@pytest.mark.parametrize("query", ["Café", "cafe", "cafe\u0301", "caf.*", "absent"])
def test_query_is_literal_case_and_accent_sensitive(query: str) -> None:
    """No normalization, case folding, regular-expression syntax or inference is applied."""
    # Arrange
    row = text_row("café")
    # Act
    report = search_evidence(RunStatus.COMPLETE, (row.specification,), (row,), query)
    # Assert
    assert report.matches == () and not report.more_matches
    assert report.status == "complete"


def test_query_whitespace_is_not_trimmed() -> None:
    """An accepted query retains meaningful leading and trailing whitespace."""
    # Arrange
    row = text_row(" café ")
    # Act
    report = search_evidence(None, (row.specification,), (row,), " café ")
    # Assert
    assert report.query == " café " and report.matches[0].quote == " café "
    assert (report.matches[0].match_start, report.matches[0].match_end) == (0, 6)


def test_occurrences_do_not_overlap_and_exact_limit_does_not_claim_truncation() -> None:
    """Two non-overlapping occurrences are returned rather than four overlapping positions."""
    # Arrange
    row = text_row("aaaaa")
    # Act
    report = search_evidence(None, (row.specification,), (row,), "aa", 2)
    # Assert
    assert [hit.match_start for hit in report.matches] == [0, 2]
    assert not report.more_matches


def test_default_limit_discloses_additional_match_without_count_claim() -> None:
    """A fourth observed occurrence proves truncation beyond the default three matches."""
    # Arrange
    row = text_row("xx xx xx xx")
    # Act
    report = search_evidence(None, (row.specification,), (row,), "xx")
    # Assert
    assert [hit.match_start for hit in report.matches] == [0, 3, 6]
    assert report.more_matches


def test_results_follow_manifest_then_physical_page_then_offset_order() -> None:
    """Source IDs and candidate page tuple order do not accidentally determine ranking."""
    # Arrange
    text = text_row("hit hit")
    pdf = pdf_row((PdfPage(2, "hit"), PdfPage(1, "hit hit")))
    rows = (text, pdf)
    # Act
    report = search_evidence(None, tuple(row.specification for row in rows), rows, "hit", 20)
    # Assert
    assert [(hit.fixture_id, hit.page_number, hit.match_start) for hit in report.matches] == [
        ("z-text", None, 0),
        ("z-text", None, 4),
        ("a-pdf", 1, 0),
        ("a-pdf", 1, 4),
        ("a-pdf", 2, 0),
    ]
    assert report.matches[-1].excerpt == "hit"


def test_matches_never_join_documents_or_pdf_pages() -> None:
    """Text split between source units cannot become a fabricated exact passage."""
    # Arrange
    rows = (
        text_row("blue ", "first"),
        text_row("lamp", "second"),
        pdf_row((PdfPage(1, "blue "), PdfPage(2, "lamp"))),
    )
    # Act
    report = search_evidence(None, tuple(row.specification for row in rows), rows, "blue lamp")
    # Assert
    assert report.matches == ()


def test_reference_annotations_are_not_candidate_evidence() -> None:
    """An expected PDF quote that was not recovered cannot be returned as extracted evidence."""
    # Arrange
    row = pdf_row((PdfPage(1, "actual output"),))
    # Act
    report = search_evidence(None, (row.specification,), (row,), "reference-only")
    # Assert
    assert report.matches == ()


def test_partial_pdf_hit_preserves_missing_page_coverage() -> None:
    """A usable retained page must not conceal a partial extraction outcome."""
    # Arrange
    row = pdf_row(
        (PdfPage(1, "Inez garde une lampe bleue."),),
        outcome=PdfWorkerOutcome.PARTIAL,
        missing_pages=(2,),
    )
    # Act
    report = search_evidence(RunStatus.COMPLETE, (row.specification,), (row,), "lampe bleue")
    # Assert
    assert report.matches[0].page_number == 1
    assert (report.matches[0].match_start, report.matches[0].match_end) == (15, 26)
    (coverage,) = report.coverage
    assert coverage.outcome == "partial" and coverage.retained_pages == (1,)
    assert coverage.total_pages == 2 and coverage.missing_pages == (2,)


def test_pdf_failure_has_unknown_missing_pages_without_a_total() -> None:
    """An early parser failure cannot imply that all pages were successfully covered."""
    # Arrange
    row = pdf_row((), outcome=PdfWorkerOutcome.CANDIDATE_FAILURE, total_pages=None)
    # Act
    report = search_evidence(None, (row.specification,), (row,), "query")
    # Assert
    (coverage,) = report.coverage
    assert coverage.outcome == "candidate_failure" and not coverage.text_available
    assert coverage.total_pages is None and coverage.missing_pages is None
    assert coverage.retained_pages == ()


def test_blank_retained_page_has_no_searchable_text() -> None:
    """Known retained blank pages differ from unavailable evidence but yield no query hit."""
    # Arrange
    row = pdf_row((PdfPage(1, ""),), outcome=PdfWorkerOutcome.NO_TEXT, total_pages=1)
    # Act
    report = search_evidence(None, (row.specification,), (row,), "query")
    # Assert
    (coverage,) = report.coverage
    assert not coverage.text_available and coverage.retained_pages == (1,)
    assert coverage.missing_pages == () and report.matches == ()


def test_missing_unfinished_and_failed_rows_remain_in_coverage() -> None:
    """Unknown, cancelled and failed observations remain visible beside a completed hit."""
    # Arrange
    good = text_row("hit")
    unfinished = FixtureRun(good.specification, unfinished_reason=RunStatus.CANCELLED)
    failure = replace(
        good, result=WorkerResult(WorkerOutcome.TIMEOUT, good.specification.sha256, None)
    )
    rows = (good, None, unfinished, failure)
    # Act
    report = search_evidence(None, (good.specification,) * 4, rows, "hit")
    # Assert
    assert len(report.matches) == 1 and report.status == "incomplete"
    assert [coverage.outcome for coverage in report.coverage] == [
        "success",
        "unknown",
        "unfinished",
        "timeout",
    ]
    assert report.coverage[2].unfinished_reason == "cancelled"
    assert all(not coverage.text_available for coverage in report.coverage[1:])


@pytest.mark.parametrize("query", ["", " \r\n\t", "a" * 201])
def test_invalid_query_is_rejected_before_search(query: str) -> None:
    """Blank and oversized expressions fail rather than matching every source position."""
    # Arrange
    # Act
    with pytest.raises(ValueError, match="query must"):
        search_evidence(None, (), (), query)
    # Assert: no match iterator was returned.


@pytest.mark.parametrize("limit", [0, -1, 21, True])
def test_invalid_limit_is_rejected_before_search(limit: int) -> None:
    """Out-of-range limits and bool-as-int inputs cannot bypass the output guard."""
    # Arrange
    # Act
    with pytest.raises(ValueError, match="limit must"):
        search_evidence(None, (), (), "query", limit)
    # Assert: no unbounded search was attempted.


def test_nonstring_query_is_rejected_by_the_public_boundary() -> None:
    """A malformed direct caller receives a safe validation error, not a text operation."""
    # Arrange
    query = cast(str, None)
    # Act
    with pytest.raises(ValueError, match="query must"):
        search_evidence(None, (), (), query)
    # Assert: no source evidence was touched.


def test_small_limit_cannot_hide_metadata_alignment_failure() -> None:
    """Coverage validates the full row alignment even when the first source fills the limit."""
    # Arrange
    row = text_row("hit hit")
    # Act
    with pytest.raises(ValueError):
        search_evidence(None, (row.specification,), (row, row), "hit", 1)
    # Assert: no truncated report masks the extra row.
