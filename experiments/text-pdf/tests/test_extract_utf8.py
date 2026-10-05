"""Success and failure scenarios for exact in-memory UTF-8 decoding."""

import pytest

from soulkiller_text import extract_utf8

from .synthetic_sources import (
    BILINGUAL_BYTES,
    BILINGUAL_SHA256,
    BILINGUAL_TEXT,
    EMPTY_SHA256,
    INVALID_BYTES,
    INVALID_SHA256,
)


def test_bilingual_source_retains_exact_text_and_original_hash() -> None:
    # Arrange
    source = BILINGUAL_BYTES

    # Act
    result = extract_utf8(source)

    # Assert
    assert result.outcome == "success"
    assert result.text == BILINGUAL_TEXT
    assert result.source_sha256 == BILINGUAL_SHA256


@pytest.mark.parametrize(
    ("source", "expected_text"),
    [
        pytest.param(b"first\r\nsecond\n", "first\r\nsecond\n", id="mixed-line-endings"),
        pytest.param(b"\xef\xbb\xbfhello", "\ufeffhello", id="bom-is-retained"),
        pytest.param(b"left\x00right", "left\x00right", id="nul-is-retained"),
        pytest.param(b"e\xcc\x81", "e\u0301", id="combining-mark-is-not-normalized"),
        pytest.param(b"\xf0\x9f\x8c\x9f", "\U0001f31f", id="non-bmp-character"),
        pytest.param(b" \t\r\n", " \t\r\n", id="whitespace-is-text"),
    ],
)
def test_valid_special_codepoints_are_preserved(source: bytes, expected_text: str) -> None:
    # Arrange
    original_bytes = source

    # Act
    result = extract_utf8(original_bytes)

    # Assert
    assert result.outcome == "success"
    assert result.text == expected_text


def test_empty_source_has_no_text_and_retains_empty_hash() -> None:
    # Arrange
    source = b""

    # Act
    result = extract_utf8(source)

    # Assert
    assert result.outcome == "no_text"
    assert result.text is None
    assert result.source_sha256 == EMPTY_SHA256


def test_invalid_source_has_no_decoded_text_and_retains_original_hash() -> None:
    # Arrange
    source = INVALID_BYTES

    # Act
    result = extract_utf8(source)

    # Assert
    assert result.outcome == "invalid_encoding"
    assert result.text is None
    assert result.source_sha256 == INVALID_SHA256


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(b"caf\xe9", id="latin-1-is-not-guessed"),
        pytest.param(b"\xc0\xaf", id="overlong-sequence-is-rejected"),
        pytest.param(b"\xed\xa0\x80", id="surrogate-is-rejected"),
        pytest.param(b"\xf0\x9f", id="truncated-sequence-is-rejected"),
    ],
)
def test_invalid_utf8_is_never_replaced_or_reinterpreted(source: bytes) -> None:
    # Arrange
    original_bytes = source

    # Act
    result = extract_utf8(original_bytes)

    # Assert
    assert result.outcome == "invalid_encoding"
    assert result.text is None
