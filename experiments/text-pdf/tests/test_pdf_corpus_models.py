"""Frozen value records retain independently declared PDF expectations."""

from dataclasses import FrozenInstanceError

import pytest

from soulkiller_text.evaluation_manifest import parse_evaluation_manifest
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation

from .corpus_helpers import encode_manifest
from .pdf_corpus_fixtures import evaluation_document


@pytest.mark.parametrize(
    "field",
    [
        "fixture_id",
        "path",
        "sha256",
        "format",
        "language",
        "author_label",
        "subject_label",
        "outcome",
        "annotations",
        "page_count",
    ],
)
def test_pdf_corpus_metadata_fields_are_immutable(field: str) -> None:
    # Arrange
    record = parse_evaluation_manifest(encode_manifest(evaluation_document()))[0]
    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(record, field, None)
    # Assert
    assert isinstance(record, PdfCorpusFixture)
    assert record.page_count == 2


@pytest.mark.parametrize("field", ["page_number", "quote"])
def test_pdf_fact_annotation_fields_are_immutable(field: str) -> None:
    # Arrange
    annotation = PdfFactAnnotation(2, "An independent statement.")
    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(annotation, field, None)
    # Assert
    assert annotation == PdfFactAnnotation(2, "An independent statement.")
