"""Native PDF outcomes and page attribution from independent invented fixtures."""

import hashlib
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pypdf
import pytest

from soulkiller_text.native_pdf import extract_native_pdf
from soulkiller_text.pdf_outcome import PdfOutcome
from soulkiller_text.synthetic_pdf import build_image_pdf, build_text_pdf

from .pdf_fixtures import (
    ENGLISH_FACT_PAGES,
    ENGLISH_PAGES,
    FRENCH_FACT_PAGES,
    FRENCH_PAGES,
    MALFORMED_PDF_SOURCES,
    protected_pdf,
)


@pytest.mark.parametrize(
    ("pages", "fact_pages"),
    [(FRENCH_PAGES, FRENCH_FACT_PAGES), (ENGLISH_PAGES, ENGLISH_FACT_PAGES)],
    ids=["french", "english"],
)
def test_independent_bilingual_facts_resolve_to_physical_source_pages(
    pages: tuple[str, ...], fact_pages: tuple[tuple[str, int], ...]
) -> None:
    # Arrange
    source = build_text_pdf(pages)
    expected_hash = hashlib.sha256(source).hexdigest()
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    assert result.source_sha256 == expected_hash
    assert result.total_pages == 2
    assert result.missing_pages == ()
    assert tuple(page.page_number for page in result.pages) == (1, 2)
    assert tuple(page.text for page in result.pages) == pages
    for fact, source_page in fact_pages:
        assert fact in result.pages[source_page - 1].text


@pytest.mark.parametrize("text", ["", "   "], ids=["blank", "whitespace"])
def test_no_meaningful_native_text_retains_covered_page(text: str) -> None:
    # Arrange
    source = build_text_pdf((text,))
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.NO_TEXT
    assert result.total_pages == 1
    assert result.missing_pages == ()
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == text


def test_image_only_page_reports_no_native_text_without_ocr() -> None:
    # Arrange
    source = build_image_pdf()
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.NO_TEXT
    assert result.total_pages == 1
    assert result.missing_pages == ()
    assert result.pages[0].page_number == 1
    assert result.pages[0].text == ""


def test_completed_mixed_document_preserves_blank_pages() -> None:
    # Arrange
    source = build_text_pdf(("Invented first-page fact.", ""))
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    assert result.total_pages == 2
    assert result.missing_pages == ()
    assert tuple(page.page_number for page in result.pages) == (1, 2)
    assert result.pages[1].text == ""


@pytest.mark.parametrize("password", ["invented-protection", ""])
def test_detected_protection_is_rejected_without_supplied_password(password: str) -> None:
    # Arrange
    source = protected_pdf(build_text_pdf(("Invented protected fact.",)), password)
    expected_hash = hashlib.sha256(source).hexdigest()
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.ENCRYPTED_PDF
    assert result.source_sha256 == expected_hash
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()


@pytest.mark.parametrize("source", MALFORMED_PDF_SOURCES)
def test_malformed_source_has_explicit_safe_outcome(source: bytes) -> None:
    # Arrange
    expected_hash = hashlib.sha256(source).hexdigest()
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.MALFORMED_INPUT
    assert result.source_sha256 == expected_hash
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()


def test_exact_twenty_page_ceiling_accepts_independent_facts() -> None:
    # Arrange
    pages = tuple(f"Invented fact on physical page {number}." for number in range(1, 21))
    source = build_text_pdf(pages)
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert result.outcome is PdfOutcome.SUCCESS
    assert result.total_pages == 20
    assert tuple(page.page_number for page in result.pages) == tuple(range(1, 21))
    assert tuple(page.text for page in result.pages) == pages


@pytest.mark.parametrize(("count", "ceiling"), [(21, 20), (3, 2)])
def test_actual_page_count_above_ceiling_is_rejected(count: int, ceiling: int) -> None:
    # Arrange
    source = build_text_pdf(tuple("Invented fact." for _ in range(count)))
    # Act
    result = extract_native_pdf(source, max_pages=ceiling)
    # Assert
    assert result.outcome is PdfOutcome.PAGE_LIMIT
    assert result.total_pages == count
    assert result.pages == ()
    assert result.missing_pages == ()


@pytest.mark.parametrize(
    "source", [bytearray(b"pdf"), memoryview(b"pdf"), "pdf", None, Path("pdf")]
)
def test_non_immutable_bytes_are_rejected_before_parsing(
    source: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    invalid_source = cast(bytes, source)
    parser = Mock()
    monkeypatch.setattr(pypdf, "PdfReader", parser)
    # Act / Assert
    with pytest.raises(TypeError, match="invalid_pdf_source"):
        extract_native_pdf(invalid_source)
    parser.assert_not_called()


def test_oversized_source_is_rejected_before_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    source = b"x" * (5 * 1024 * 1024 + 1)
    parser = Mock()
    monkeypatch.setattr(pypdf, "PdfReader", parser)
    # Act / Assert
    with pytest.raises(ValueError, match="pdf_input_too_large"):
        extract_native_pdf(source)
    parser.assert_not_called()


@pytest.mark.parametrize("ceiling", [0, -1, 21, True, 1.0, "2", None])
def test_invalid_page_ceiling_is_rejected(ceiling: object, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    source = build_text_pdf(("Invented fact.",))
    parser = Mock()
    monkeypatch.setattr(pypdf, "PdfReader", parser)
    # Act / Assert
    with pytest.raises(ValueError, match="invalid_pdf_page_limit"):
        extract_native_pdf(source, max_pages=cast(int, ceiling))
    parser.assert_not_called()


def test_independent_valid_fixture_is_eligible_after_malformed_outcome() -> None:
    # Arrange
    sources = (b"not a PDF", build_text_pdf(("A separate invented fact.",)))
    # Act
    results = tuple(extract_native_pdf(source) for source in sources)
    # Assert
    assert tuple(result.outcome for result in results) == (
        PdfOutcome.MALFORMED_INPUT,
        PdfOutcome.SUCCESS,
    )
    assert results[1].pages[0].text == "A separate invented fact."


def test_extraction_preserves_exact_immutable_source_revision() -> None:
    # Arrange
    source = build_text_pdf(FRENCH_PAGES)
    original_bytes = bytes(bytearray(source))
    # Act
    result = extract_native_pdf(source)
    # Assert
    assert source == original_bytes
    assert result.source_sha256 == hashlib.sha256(original_bytes).hexdigest()
