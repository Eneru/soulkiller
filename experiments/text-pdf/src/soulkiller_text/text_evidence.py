"""A source-linked quote with Unicode code-point offsets."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextEvidence:
    """Represent a zero-based, end-exclusive slice of decoded source text."""

    source_sha256: str
    start: int
    end: int
    quote: str
