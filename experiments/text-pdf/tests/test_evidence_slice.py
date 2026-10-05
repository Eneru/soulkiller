"""Source-resolving code-point quotes and rejected evidence references."""

from typing import cast

import pytest

from soulkiller_text import ExtractionResult, evidence_slice, extract_utf8

from .synthetic_sources import CODEPOINT_TEXT, INVALID_BYTES


def test_quote_counts_codepoints_and_retains_original_source_reference(
    successful_extraction: ExtractionResult,
) -> None:
    # Arrange
    source = successful_extraction

    # Act
    evidence = evidence_slice(source, 1, 6)

    # Assert
    assert evidence.source_sha256 == source.source_sha256
    assert evidence.start == 1
    assert evidence.end == 6
    assert evidence.quote == "é e\u0301\U0001f31f"
    assert source.text is not None
    assert evidence.quote == source.text[evidence.start : evidence.end]


@pytest.mark.parametrize(
    ("start", "end", "expected_quote"),
    [
        pytest.param(0, 7, CODEPOINT_TEXT, id="whole-source"),
        pytest.param(0, 1, "A", id="first-codepoint"),
        pytest.param(6, 7, "Z", id="last-codepoint"),
        pytest.param(4, 5, "\u0301", id="combining-codepoint-is-addressable"),
        pytest.param(5, 6, "\U0001f31f", id="non-bmp-is-one-codepoint"),
    ],
)
def test_boundary_spans_return_exact_quotes(
    successful_extraction: ExtractionResult,
    start: int,
    end: int,
    expected_quote: str,
) -> None:
    # Arrange
    source = successful_extraction

    # Act
    evidence = evidence_slice(source, start, end)

    # Assert
    assert evidence.quote == expected_quote


@pytest.mark.parametrize(
    ("start", "end"),
    [
        pytest.param(True, 3, id="boolean-start"),
        pytest.param(0, False, id="boolean-end"),
        pytest.param(1.0, 3, id="float-start"),
        pytest.param(0, 3.0, id="float-end"),
        pytest.param("1", 3, id="string-start"),
        pytest.param(0, None, id="missing-end"),
    ],
)
def test_noninteger_offsets_are_rejected(
    successful_extraction: ExtractionResult, start: object, end: object
) -> None:
    # Arrange
    source = successful_extraction

    # Act / Assert: casts deliberately exercise invalid callers.
    with pytest.raises(TypeError, match="must be integers"):
        evidence_slice(source, cast(int, start), cast(int, end))


@pytest.mark.parametrize(
    ("start", "end"),
    [
        pytest.param(-1, 1, id="negative-start"),
        pytest.param(0, -1, id="negative-end"),
        pytest.param(1, 1, id="empty-span"),
        pytest.param(3, 2, id="reversed-span"),
        pytest.param(0, 8, id="end-past-source"),
        pytest.param(8, 9, id="start-past-source"),
    ],
)
def test_invalid_spans_are_rejected(
    successful_extraction: ExtractionResult, start: int, end: int
) -> None:
    # Arrange
    source = successful_extraction

    # Act / Assert
    with pytest.raises(ValueError, match="nonempty span within"):
        evidence_slice(source, start, end)


@pytest.mark.parametrize(
    "source_bytes",
    [
        pytest.param(b"", id="no-text-outcome"),
        pytest.param(INVALID_BYTES, id="invalid-encoding-outcome"),
    ],
)
def test_nonsuccess_outcomes_cannot_produce_evidence(source_bytes: bytes) -> None:
    # Arrange
    source = extract_utf8(source_bytes)

    # Act / Assert
    with pytest.raises(ValueError, match="successful extraction"):
        evidence_slice(source, 0, 1)
