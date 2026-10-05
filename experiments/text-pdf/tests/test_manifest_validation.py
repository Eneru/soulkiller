"""Independent strict schema, JSON, uniqueness and input-budget scenarios."""

import pytest

from soulkiller_text.corpus_constants import MAX_ANNOTATIONS, MAX_FIXTURES, MAX_MANIFEST_BYTES
from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.manifest_validation import parse_manifest
from soulkiller_text.text_annotation import TextAnnotation

from .corpus_helpers import (
    annotation_document,
    encode_manifest,
    fixture_document,
    manifest_document,
)


def test_valid_manifest_preserves_explicit_labels_and_literal_annotation() -> None:
    # Arrange
    fixture = fixture_document()
    fixture["author_label"] = "  Invented author  "
    fixture["subject_label"] = "An explicitly different subject"
    source = encode_manifest(manifest_document([fixture]))

    # Act
    result = parse_manifest(source)

    # Assert
    assert len(result) == 1
    assert result[0].fixture_id == "sample"
    assert result[0].path == "texts/sample.txt"
    assert result[0].format == "txt"
    assert result[0].language == "en"
    assert result[0].author_label == "  Invented author  "
    assert result[0].subject_label == "An explicitly different subject"
    assert result[0].annotations == (TextAnnotation(0, 3, "abc"),)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(b"\xff", id="invalid-utf8"),
        pytest.param(b'{"private-input"', id="malformed-json"),
        pytest.param(b"[" * 2000 + b"0" + b"]" * 2000, id="deep-json"),
        pytest.param(b"\xef\xbb\xbf{}", id="json-bom"),
        pytest.param(b"", id="empty-json"),
    ],
)
def test_invalid_json_or_encoding_has_no_input_details_in_error(source: bytes) -> None:
    # Arrange
    manifest_bytes = source

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(manifest_bytes)

    # Assert
    assert failure.value.category == "invalid_manifest"
    assert failure.value.args == ("invalid_manifest",)


@pytest.mark.parametrize(
    ("needle", "replacement"),
    [
        pytest.param(
            b'"schema_version":1', b'"schema_version":1,"schema_version":1', id="root-key"
        ),
        pytest.param(b'"id":"sample"', b'"id":"sample","id":"sample"', id="fixture-key"),
        pytest.param(b'"start":0', b'"start":0,"start":0', id="annotation-key"),
    ],
)
def test_duplicate_json_keys_are_rejected_even_when_values_agree(
    needle: bytes, replacement: bytes
) -> None:
    # Arrange
    source = encode_manifest(manifest_document()).replace(needle, replacement, 1)

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)

    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "version",
    [
        pytest.param(True, id="boolean"),
        pytest.param(1.0, id="float"),
        pytest.param("1", id="string"),
        pytest.param(2, id="unsupported-version"),
        pytest.param(None, id="null"),
        pytest.param(float("nan"), id="nonfinite-nan"),
        pytest.param(float("inf"), id="nonfinite-infinity"),
        pytest.param(float("-inf"), id="nonfinite-negative-infinity"),
    ],
)
def test_schema_version_requires_integer_one(version: object) -> None:
    # Arrange
    document = manifest_document()
    document["schema_version"] = version

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(encode_manifest(document))

    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "document",
    [
        pytest.param([], id="array-root"),
        pytest.param(None, id="null-root"),
        pytest.param({"schema_version": 1}, id="missing-fixtures"),
        pytest.param({"fixtures": []}, id="missing-version"),
        pytest.param({"schema_version": 1, "fixtures": [], "extra": 1}, id="unknown-root-key"),
        pytest.param({"schema_version": 1, "fixtures": {}}, id="nonlist-fixtures"),
        pytest.param({"schema_version": 1, "fixtures": []}, id="empty-fixtures"),
        pytest.param({"schema_version": 1, "fixtures": [None]}, id="nonobject-fixture"),
    ],
)
def test_root_shape_and_exact_fields_are_required(document: object) -> None:
    # Arrange
    source = encode_manifest(document)

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)

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
        "outcome",
        "annotations",
    ],
)
def test_every_fixture_field_is_required(field: str) -> None:
    # Arrange
    fixture = fixture_document()
    del fixture[field]
    source = encode_manifest(manifest_document([fixture]))

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)

    # Assert
    assert failure.value.category == "invalid_manifest"


def test_unknown_fixture_fields_are_rejected() -> None:
    # Arrange
    fixture = fixture_document()
    fixture["private-extra"] = "never report this value"
    source = encode_manifest(manifest_document([fixture]))

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)

    # Assert
    assert failure.value.args == ("invalid_manifest",)


@pytest.mark.parametrize(
    ("field", "value", "category"),
    [
        pytest.param("id", "", "invalid_manifest", id="empty-id"),
        pytest.param("id", "x" * 65, "invalid_manifest", id="long-id"),
        pytest.param("id", "é", "invalid_manifest", id="nonascii-id"),
        pytest.param("id", "-first", "invalid_manifest", id="invalid-id-start"),
        pytest.param("id", "two words", "invalid_manifest", id="invalid-id-character"),
        pytest.param("path", "../secret.txt", "invalid_path", id="escaping-path"),
        pytest.param("path", "manifest.json", "invalid_path", id="manifest-as-source"),
        pytest.param("path", None, "invalid_path", id="nonstring-path"),
        pytest.param("sha256", "a" * 63, "invalid_manifest", id="short-hash"),
        pytest.param("sha256", "A" * 64, "invalid_manifest", id="uppercase-hash"),
        pytest.param("sha256", "g" * 64, "invalid_manifest", id="nonhex-hash"),
        pytest.param("format", "pdf", "invalid_manifest", id="unsupported-format"),
        pytest.param("language", "de", "invalid_manifest", id="unsupported-language"),
        pytest.param("author_label", "", "invalid_manifest", id="empty-author"),
        pytest.param("author_label", "x" * 129, "invalid_manifest", id="long-author"),
        pytest.param("subject_label", "", "invalid_manifest", id="empty-subject"),
        pytest.param("subject_label", "x" * 129, "invalid_manifest", id="long-subject"),
        pytest.param("subject_label", "\ud800", "invalid_manifest", id="surrogate-label"),
        pytest.param("outcome", "partial", "invalid_manifest", id="unknown-outcome"),
        pytest.param("annotations", None, "invalid_manifest", id="nonlist-annotations"),
    ],
)
def test_invalid_fixture_values_have_stable_categories(
    field: str, value: object, category: str
) -> None:
    # Arrange
    fixture = fixture_document()
    fixture[field] = value
    source = encode_manifest(manifest_document([fixture]))

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(source)

    # Assert
    assert failure.value.category == category


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("id", "A" + "_" * 63, id="maximum-id"),
        pytest.param("language", "fr", id="french-language"),
        pytest.param("author_label", "🌟" * 128, id="maximum-unicode-label"),
        pytest.param("subject_label", "x" * 128, id="maximum-subject"),
    ],
)
def test_valid_fixture_value_boundaries_are_preserved(field: str, value: str) -> None:
    # Arrange
    fixture = fixture_document()
    fixture[field] = value
    source = encode_manifest(manifest_document([fixture]))

    # Act
    result = parse_manifest(source)

    # Assert
    attribute = "fixture_id" if field == "id" else field
    assert getattr(result[0], attribute) == value


@pytest.mark.parametrize(
    ("field", "value"),
    [
        pytest.param("start", True, id="boolean-start"),
        pytest.param("end", False, id="boolean-end"),
        pytest.param("start", 1.0, id="float-offset"),
        pytest.param("start", -1, id="negative-offset"),
        pytest.param("start", 3, id="empty-span"),
        pytest.param("end", 0, id="empty-end"),
        pytest.param("start", 4, id="reversed-span"),
        pytest.param("quote", "", id="empty-quote"),
        pytest.param("quote", None, id="nonstring-quote"),
        pytest.param("quote", "\ud800", id="surrogate-quote"),
    ],
)
def test_invalid_annotation_values_are_rejected(field: str, value: object) -> None:
    # Arrange
    annotation = annotation_document()
    annotation[field] = value
    fixture = fixture_document()
    fixture["annotations"] = [annotation]

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(encode_manifest(manifest_document([fixture])))

    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize(
    "annotation",
    [
        pytest.param(None, id="nonobject-annotation"),
        pytest.param({"start": 0, "end": 3}, id="missing-quote"),
        pytest.param({"start": 0, "quote": "abc"}, id="missing-end"),
        pytest.param({"end": 3, "quote": "abc"}, id="missing-start"),
        pytest.param({"start": 0, "end": 3, "quote": "abc", "extra": 1}, id="unknown-field"),
    ],
)
def test_annotation_fields_are_exact(annotation: object) -> None:
    # Arrange
    fixture = fixture_document()
    fixture["annotations"] = [annotation]

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(encode_manifest(manifest_document([fixture])))

    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("outcome", ["no_text", "invalid_encoding"])
def test_nonsuccess_outcomes_reject_annotations(outcome: str) -> None:
    # Arrange
    fixture = fixture_document()
    fixture["outcome"] = outcome

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(encode_manifest(manifest_document([fixture])))

    # Assert
    assert failure.value.category == "invalid_manifest"


@pytest.mark.parametrize("outcome", ["no_text", "invalid_encoding"])
def test_nonsuccess_outcomes_allow_no_annotations(outcome: str) -> None:
    # Arrange
    fixture = fixture_document()
    fixture["outcome"] = outcome
    fixture["annotations"] = []

    # Act
    result = parse_manifest(encode_manifest(manifest_document([fixture])))

    # Assert
    assert result[0].outcome == outcome
    assert result[0].annotations == ()


@pytest.mark.parametrize("duplicate", ["id", "path"])
def test_duplicate_fixture_identifiers_or_paths_are_rejected(duplicate: str) -> None:
    # Arrange
    first = fixture_document()
    second = fixture_document("other", "texts/other.txt")
    second[duplicate] = first[duplicate]

    # Act
    with pytest.raises(CorpusError) as failure:
        parse_manifest(encode_manifest(manifest_document([first, second])))

    # Assert
    assert failure.value.category == "duplicate_fixture"


@pytest.mark.parametrize("count", [MAX_FIXTURES, MAX_FIXTURES + 1])
def test_fixture_count_is_bounded(count: int) -> None:
    # Arrange
    fixtures = [fixture_document(f"item-{index}", f"texts/{index}.txt") for index in range(count)]
    source = encode_manifest(manifest_document(fixtures))

    # Act / Assert
    if count == MAX_FIXTURES:
        assert len(parse_manifest(source)) == MAX_FIXTURES
    else:
        with pytest.raises(CorpusError, match="^invalid_manifest$"):
            parse_manifest(source)


@pytest.mark.parametrize("count", [MAX_ANNOTATIONS, MAX_ANNOTATIONS + 1])
def test_annotation_count_is_bounded(count: int) -> None:
    # Arrange
    fixture = fixture_document()
    fixture["annotations"] = [annotation_document() for _ in range(count)]
    source = encode_manifest(manifest_document([fixture]))

    # Act / Assert
    if count == MAX_ANNOTATIONS:
        assert len(parse_manifest(source)[0].annotations) == MAX_ANNOTATIONS
    else:
        with pytest.raises(CorpusError, match="^invalid_manifest$"):
            parse_manifest(source)


@pytest.mark.parametrize("overflow", [False, True])
def test_manifest_byte_ceiling_includes_valid_trailing_whitespace(overflow: bool) -> None:
    # Arrange
    baseline = encode_manifest(manifest_document())
    source = baseline + b" " * (MAX_MANIFEST_BYTES - len(baseline) + int(overflow))

    # Act / Assert
    if overflow:
        with pytest.raises(CorpusError, match="^manifest_too_large$"):
            parse_manifest(source)
    else:
        assert len(parse_manifest(source)) == 1
