"""An answer observation separated from locally retained source evidence."""

from dataclasses import dataclass

from .source_match import SourceMatch


@dataclass(frozen=True)
class AnswerResult:
    """Citation IDs index the immutable supplied source tuple, never model-supplied paths."""

    status: str
    text: str
    citations: tuple[str, ...]
    sources: tuple[SourceMatch, ...]
    backend: str
