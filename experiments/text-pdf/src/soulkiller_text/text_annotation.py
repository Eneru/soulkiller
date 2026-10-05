"""An independently authored code-point annotation."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TextAnnotation:
    """Retain a zero-based, end-exclusive expected source quote."""

    start: int
    end: int
    quote: str
