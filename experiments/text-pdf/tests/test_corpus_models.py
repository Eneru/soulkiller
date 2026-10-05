"""Frozen validated metadata and source snapshots cannot be edited in place."""

from dataclasses import FrozenInstanceError

import pytest

from soulkiller_text.loaded_fixture import LoadedFixture
from soulkiller_text.manifest_validation import parse_manifest
from soulkiller_text.text_annotation import TextAnnotation

from .corpus_helpers import encode_manifest, manifest_document


@pytest.mark.parametrize("attribute", ["start", "end", "quote"])
def test_text_annotation_is_immutable(attribute: str) -> None:
    # Arrange
    annotation = TextAnnotation(0, 3, "abc")

    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(annotation, attribute, None)

    # Assert
    assert annotation == TextAnnotation(0, 3, "abc")


@pytest.mark.parametrize("attribute", ["fixture_id", "annotations", "author_label"])
def test_corpus_fixture_is_immutable(attribute: str) -> None:
    # Arrange
    fixture = parse_manifest(encode_manifest(manifest_document()))[0]

    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(fixture, attribute, None)

    # Assert
    assert fixture.fixture_id == "sample"
    assert fixture.annotations == (TextAnnotation(0, 3, "abc"),)


@pytest.mark.parametrize("attribute", ["specification", "source"])
def test_loaded_fixture_is_immutable(attribute: str) -> None:
    # Arrange
    fixture = parse_manifest(encode_manifest(manifest_document()))[0]
    loaded = LoadedFixture(fixture, b"abc")

    # Act
    with pytest.raises(FrozenInstanceError):
        setattr(loaded, attribute, None)

    # Assert
    assert loaded.specification == fixture
    assert loaded.source == b"abc"
