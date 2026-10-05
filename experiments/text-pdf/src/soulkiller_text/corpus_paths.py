"""Validate relative slash paths without interpreting or opening them."""

from .corpus_error import CorpusError


def validate_relative_path(value: str) -> tuple[str, ...]:
    """Return unchanged components or raise CorpusError('invalid_path')."""
    if (
        not isinstance(value, str)
        or not value
        or any(character in value for character in ("\\", ":", "\x00"))
        or any(0xD800 <= ord(character) <= 0xDFFF for character in value)
    ):
        raise CorpusError("invalid_path")

    components = tuple(value.split("/"))
    if any(component in ("", ".", "..") for component in components):
        raise CorpusError("invalid_path")

    return components
