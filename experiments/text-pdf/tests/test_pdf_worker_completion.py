"""Supervisor observations override candidate claims and discard evidence."""

import pytest

from soulkiller_text.pdf_worker_completion import classify_completion
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.worker_outcome import WorkerOutcome

from .pdf_worker_fixtures import pdf_payload
from .synthetic_sources import BILINGUAL_SHA256


@pytest.mark.parametrize(
    ("code", "failure", "expected"),
    [
        (0, WorkerOutcome.TIMEOUT, "timeout"),
        (3, WorkerOutcome.TIMEOUT, "timeout"),
        (4, WorkerOutcome.OUTPUT_LIMIT, "output_limit"),
        (None, None, "timeout"),
        (3, None, "unsupported_environment"),
        (4, None, "resource_limit"),
        (1, None, "candidate_failure"),
        (-9, None, "candidate_failure"),
        (0, WorkerOutcome.CANDIDATE_FAILURE, "candidate_failure"),
    ],
)
def test_observed_failure_takes_precedence_over_apparent_success(
    code: int | None, failure: WorkerOutcome | None, expected: str
) -> None:
    # Arrange
    response = pdf_payload()
    # Act
    result = classify_completion(code, failure, response, BILINGUAL_SHA256)
    # Assert
    assert result.outcome == expected
    assert isinstance(result.outcome, PdfWorkerOutcome)
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()


def test_completed_response_preserves_verified_pages() -> None:
    # Arrange
    response = pdf_payload()
    # Act
    result = classify_completion(0, None, response, BILINGUAL_SHA256)
    # Assert
    assert result.outcome is PdfWorkerOutcome.SUCCESS
    assert result.pages[0].page_number == 1


@pytest.mark.parametrize("response", [b"not json", pdf_payload(source_sha256="0" * 64)])
def test_protocol_failure_retains_only_parent_hash(response: bytes) -> None:
    # Arrange
    expected_hash = BILINGUAL_SHA256
    # Act
    result = classify_completion(0, None, response, expected_hash)
    # Assert
    assert result.outcome is PdfWorkerOutcome.PROTOCOL_ERROR
    assert result.source_sha256 == expected_hash
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()
