"""Immutable PDF value records and explicit stable outcome names."""

from dataclasses import FrozenInstanceError

import pytest

from soulkiller_text.pdf_outcome import PdfOutcome
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_result import PdfResult


@pytest.mark.parametrize("attribute", ["page_number", "text"])
def test_covered_page_record_is_immutable(attribute: str) -> None:
    # Arrange
    page = PdfPage(2, "Invented text.")
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(page, attribute, "changed")


@pytest.mark.parametrize(
    "attribute", ["outcome", "source_sha256", "pages", "total_pages", "missing_pages"]
)
def test_pdf_result_record_is_immutable(attribute: str) -> None:
    # Arrange
    result = PdfResult(PdfOutcome.PARTIAL, "a" * 64, (PdfPage(2, "Invented text."),), 2, (1,))
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(result, attribute, "changed")


@pytest.mark.parametrize(
    ("outcome", "value"),
    [
        (PdfOutcome.SUCCESS, "success"),
        (PdfOutcome.NO_TEXT, "no_text"),
        (PdfOutcome.ENCRYPTED_PDF, "encrypted_pdf"),
        (PdfOutcome.MALFORMED_INPUT, "malformed_input"),
        (PdfOutcome.PAGE_LIMIT, "page_limit"),
        (PdfOutcome.PARTIAL, "partial"),
        (PdfOutcome.UNSUPPORTED_DEPENDENCY, "unsupported_dependency"),
        (PdfOutcome.CANDIDATE_FAILURE, "candidate_failure"),
    ],
)
def test_explicit_pdf_outcomes_retain_string_interoperability(
    outcome: PdfOutcome, value: str
) -> None:
    # Arrange
    stable_value = value
    # Act
    parsed = PdfOutcome(stable_value)
    # Assert
    assert parsed is outcome
    assert outcome == stable_value
    assert str(outcome) == stable_value
