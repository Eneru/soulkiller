"""Independent PDF writer checks for validity, escaping and fixture boundaries."""

from io import BytesIO

import pytest
from pypdf import PdfReader

from soulkiller_text.synthetic_pdf import build_image_pdf, build_text_pdf

from .pdf_fixtures import ENGLISH_PAGES, FRENCH_PAGES, protected_pdf


@pytest.mark.parametrize("pages", [FRENCH_PAGES, ENGLISH_PAGES])
def test_text_fixture_is_deterministic_and_has_independent_page_text(
    pages: tuple[str, ...],
) -> None:
    # Arrange
    expected_pages = pages
    # Act
    source = build_text_pdf(expected_pages)
    reader = PdfReader(BytesIO(source), strict=True)
    # Assert
    assert build_text_pdf(expected_pages) == source
    assert len(reader.pages) == len(expected_pages)
    for page, expected in zip(reader.pages, expected_pages, strict=True):
        assert page.extract_text(extraction_mode="plain") == expected


def test_pdf_literal_escaping_preserves_parentheses_backslashes_and_accents() -> None:
    # Arrange
    expected = "Émile écrit (bonjour) dans C:\\invented\\café."
    # Act
    source = build_text_pdf((expected,))
    reader = PdfReader(BytesIO(source), strict=True)
    # Assert
    assert reader.pages[0].extract_text(extraction_mode="plain") == expected


def test_cross_reference_offsets_resolve_actual_numbered_objects() -> None:
    # Arrange
    pages = ("Invented first page.", "Invented second page.", "")
    # Act
    source = build_text_pdf(pages)
    xref_offset = int(source.rpartition(b"startxref\n")[2].split(b"\n", 1)[0])
    # Assert
    assert source[xref_offset:].startswith(b"xref\n")
    entries = [line for line in source[xref_offset:].splitlines()[3:] if line.endswith(b" n ")]
    assert len(entries) == 3 + 2 * len(pages)
    for number, entry in enumerate(entries, 1):
        object_offset = int(entry[:10])
        assert source[object_offset:].startswith(f"{number} 0 obj\n".encode("ascii"))


def test_image_fixture_is_deterministic_and_has_no_native_text() -> None:
    # Arrange / Act
    source = build_image_pdf()
    reader = PdfReader(BytesIO(source), strict=True)
    # Assert
    assert build_image_pdf() == source
    assert b"/Subtype /Image" in source
    assert len(reader.pages) == 1
    assert reader.pages[0].extract_text(extraction_mode="plain") == ""


def test_blank_fixture_retains_its_empty_physical_page() -> None:
    # Arrange
    pages = ("",)
    # Act
    reader = PdfReader(BytesIO(build_text_pdf(pages)), strict=True)
    # Assert
    assert len(reader.pages) == 1
    assert reader.pages[0].extract_text(extraction_mode="plain") == ""


def test_text_fixture_requires_at_least_one_page() -> None:
    # Arrange
    pages: tuple[str, ...] = ()
    # Act / Assert
    with pytest.raises(ValueError, match="synthetic_pdf_requires_pages"):
        build_text_pdf(pages)


def test_writer_rejects_text_outside_its_declared_winansi_font() -> None:
    # Arrange
    pages = ("Invented comet 🌠",)
    # Act / Assert
    with pytest.raises(UnicodeEncodeError):
        build_text_pdf(pages)


@pytest.mark.parametrize("password", ["invented-protection", ""])
def test_protected_sentinel_is_encrypted_even_with_an_empty_password(password: str) -> None:
    # Arrange
    original = build_text_pdf(("Invented protected fact.",))
    # Act
    source = protected_pdf(original, password)
    reader = PdfReader(BytesIO(source))
    # Assert
    assert reader.is_encrypted
    assert source != original
