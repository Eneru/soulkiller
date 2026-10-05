"""Returned result and evidence records cannot be edited in place."""

from dataclasses import FrozenInstanceError

import pytest

from soulkiller_text import ExtractionResult, evidence_slice, extract_utf8

from .synthetic_sources import BILINGUAL_BYTES


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        pytest.param("outcome", "no_text", id="outcome"),
        pytest.param("source_sha256", "0" * 64, id="source-hash"),
        pytest.param("text", "changed", id="decoded-text"),
    ],
)
def test_extraction_result_is_immutable(attribute: str, replacement: object) -> None:
    # Arrange
    result = extract_utf8(BILINGUAL_BYTES)

    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(result, attribute, replacement)


@pytest.mark.parametrize(
    ("attribute", "replacement"),
    [
        pytest.param("source_sha256", "0" * 64, id="source-hash"),
        pytest.param("start", 1, id="start-offset"),
        pytest.param("end", 2, id="end-offset"),
        pytest.param("quote", "changed", id="quote"),
    ],
)
def test_evidence_record_is_immutable(
    successful_extraction: ExtractionResult, attribute: str, replacement: object
) -> None:
    # Arrange
    evidence = evidence_slice(successful_extraction, 0, 1)

    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(evidence, attribute, replacement)
