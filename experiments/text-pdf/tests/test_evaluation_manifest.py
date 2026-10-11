"""Strict mixed-version schema and compatibility scenarios."""

from collections.abc import Callable

import pytest

from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.corpus_fixture import CorpusFixture
from soulkiller_text.evaluation_manifest import parse_evaluation_manifest
from soulkiller_text.manifest_validation import parse_manifest
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_fact_annotation import PdfFactAnnotation
from soulkiller_text.text_annotation import TextAnnotation

from .corpus_helpers import encode_manifest, fixture_document, manifest_document
from .pdf_corpus_fixtures import evaluation_document, pdf_document


def test_evaluation_parser_preserves_version_one_txt_contract() -> None:
    # Arrange
    source = encode_manifest(manifest_document())
    # Act
    result = parse_evaluation_manifest(source)
    # Assert
    assert result == parse_manifest(source)
    assert isinstance(result[0], CorpusFixture)
    assert result[0].annotations == (TextAnnotation(0, 3, "abc"),)


def test_mixed_manifest_retains_explicit_format_labels_and_page_facts() -> None:
    # Arrange
    source = encode_manifest(evaluation_document([fixture_document(), pdf_document()]))
    # Act
    result = parse_evaluation_manifest(source)
    # Assert
    assert len(result) == 2
    assert isinstance(result[0], CorpusFixture)
    assert isinstance(result[1], PdfCorpusFixture)
    assert result[1].format == "pdf"
    assert result[1].language == "fr"
    assert result[1].author_label == "  Inez (invented author)  "
    assert result[1].subject_label == "Corin (invented subject)"
    assert result[1].page_count == 2
    assert result[1].annotations == (PdfFactAnnotation(2, "Inez garde une lampe bleue."),)


@pytest.mark.parametrize("parser", [parse_manifest, parse_evaluation_manifest])
def test_version_one_rejects_even_complete_pdf_metadata(
    parser: Callable[[bytes], tuple[CorpusFixture | PdfCorpusFixture, ...]],
) -> None:
    # Arrange
    source = encode_manifest(manifest_document([pdf_document()]))
    # Act
    with pytest.raises(CorpusError) as failure:
        parser(source)
    # Assert
    assert failure.value.category == "invalid_manifest"


def test_txt_only_parser_still_rejects_version_two() -> None:
    # Arrange
    source = encode_manifest(evaluation_document([fixture_document()]))
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("version", [True, False, 2.0, "2", 0, 3, None])
def test_evaluation_schema_version_requires_supported_nonboolean_integer(version: object) -> None:
    # Arrange
    document = evaluation_document()
    document["schema_version"] = version
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(document))
    # Assert
    assert failure.value.args == ("invalid_manifest",)


@pytest.mark.parametrize(
    "document",
    [
        {"schema_version": 2, "fixtures": [], "extra": 0},
        {"schema_version": 2, "fixtures": []},
        {"schema_version": 2, "fixtures": {}},
        {"schema_version": 2},
        {"fixtures": []},
        [],
    ],
    ids=[
        "extra-root",
        "empty-selection",
        "nonlist",
        "missing-fixtures",
        "missing-version",
        "array",
    ],
)
def test_evaluation_root_fields_remain_exact(document: object) -> None:
    # Arrange
    source = encode_manifest(document)
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(source)
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "field",
    [
        "id",
        "path",
        "sha256",
        "format",
        "language",
        "author_label",
        "subject_label",
        "page_count",
        "outcome",
        "annotations",
    ],
)
def test_pdf_metadata_requires_every_exact_field(field: str) -> None:
    # Arrange
    fixture = pdf_document()
    del fixture[field]
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


def test_pdf_metadata_rejects_unknown_field_without_echoing_value() -> None:
    # Arrange
    fixture = pdf_document()
    fixture["private-extra"] = "Invented sensitive marker"
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.args == ("invalid_manifest",)


def test_version_two_txt_metadata_cannot_gain_pdf_page_count() -> None:
    # Arrange
    fixture = fixture_document()
    fixture["page_count"] = 1
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("id", "", "invalid_manifest"),
        ("language", "de", "invalid_manifest"),
        ("format", "PDF", "invalid_manifest"),
        ("format", None, "invalid_manifest"),
        ("sha256", "A" * 64, "invalid_manifest"),
        ("author_label", "\ud800", "invalid_manifest"),
        ("subject_label", "x" * 129, "invalid_manifest"),
        ("path", "../private.pdf", "invalid_path"),
        ("path", "manifest.json", "invalid_path"),
    ],
)
def test_pdf_common_metadata_preserves_existing_input_rules(
    field: str, value: object, category: str
) -> None:
    # Arrange
    fixture = pdf_document()
    fixture[field] = value
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == category


@pytest.mark.parametrize("duplicate", ["id", "path"])
def test_uniqueness_is_enforced_across_txt_and_pdf_entries(duplicate: str) -> None:
    # Arrange
    txt = fixture_document()
    pdf = pdf_document()
    pdf[duplicate] = txt[duplicate]
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([txt, pdf])))
    # Assert
    assert failure.value.category == "duplicate_fixture"


@pytest.mark.parametrize(
    "needle,replacement",
    [
        (b'"schema_version":2', b'"schema_version":2,"schema_version":2'),
        (b'"page_count":2', b'"page_count":2,"page_count":2'),
        (b'"page_number":2', b'"page_number":2,"page_number":2'),
    ],
)
def test_mixed_manifest_rejects_duplicate_json_keys(needle: bytes, replacement: bytes) -> None:
    # Arrange
    source = encode_manifest(evaluation_document()).replace(needle, replacement, 1)
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(source)
    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_mixed_manifest_rejects_nonstandard_json_constants(value: float) -> None:
    # Arrange
    fixture = pdf_document()
    fixture["page_count"] = value
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document([fixture])))
    # Assert
    assert failure.value.category == "invalid_manifest"


def test_mixed_selection_accepts_exactly_thirty_two_fixtures() -> None:
    # Arrange
    fixtures = [fixture_document(f"txt-{index}", f"texts/{index}.txt") for index in range(31)]
    fixtures.append(pdf_document())
    # Act
    result = parse_evaluation_manifest(encode_manifest(evaluation_document(fixtures)))
    # Assert
    assert len(result) == 32


def test_mixed_selection_rejects_thirty_three_fixtures() -> None:
    # Arrange
    fixtures = [fixture_document(f"txt-{index}", f"texts/{index}.txt") for index in range(32)]
    fixtures.append(pdf_document())
    # Act
    with pytest.raises(CorpusError) as failure:
        parse_evaluation_manifest(encode_manifest(evaluation_document(fixtures)))
    # Assert
    assert failure.value.category == "invalid_manifest"
