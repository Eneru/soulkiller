"""Relative path grammar rejects ambiguity and escapes without any I/O."""

from typing import cast

import pytest

from soulkiller_text.corpus_error import CorpusError
from soulkiller_text.corpus_paths import validate_relative_path


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        pytest.param("texts/source.txt", ("texts", "source.txt"), id="ordinary-source"),
        pytest.param("café/notes en français.txt", ("café", "notes en français.txt"), id="unicode"),
        pytest.param("source.txt", ("source.txt",), id="single-component"),
    ],
)
def test_relative_path_preserves_valid_components(path: str, expected: tuple[str, ...]) -> None:
    # Arrange
    supplied_path = path

    # Act
    components = validate_relative_path(supplied_path)

    # Assert
    assert components == expected


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("", id="empty"),
        pytest.param("/source.txt", id="absolute"),
        pytest.param(".", id="dot"),
        pytest.param("../source.txt", id="parent"),
        pytest.param("texts/./source.txt", id="interior-dot"),
        pytest.param("texts/../source.txt", id="interior-parent"),
        pytest.param("texts//source.txt", id="repeated-slash"),
        pytest.param("texts/", id="trailing-slash"),
        pytest.param("texts\\source.txt", id="backslash"),
        pytest.param("C:/source.txt", id="drive-colon"),
        pytest.param("source.txt:stream", id="stream-colon"),
        pytest.param("source\x00.txt", id="nul"),
        pytest.param("source\ud800.txt", id="surrogate"),
        pytest.param(None, id="nonstring"),
    ],
)
def test_invalid_relative_path_raises_only_a_named_category(path: object) -> None:
    # Arrange
    supplied_path = cast(str, path)

    # Act
    with pytest.raises(CorpusError) as failure:
        validate_relative_path(supplied_path)

    # Assert
    assert failure.value.category == "invalid_path"
    assert failure.value.args == ("invalid_path",)
