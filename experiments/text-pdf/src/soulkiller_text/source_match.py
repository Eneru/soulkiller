"""One literal match with a resolving exact excerpt in saved candidate text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceMatch:
    """Offsets are code points within TXT text or the named PDF page, never file bytes."""

    fixture_id: str
    path: str
    source_sha256: str
    format: str
    language: str
    author_label: str
    subject_label: str
    page_number: int | None
    match_start: int
    match_end: int
    excerpt_start: int
    excerpt_end: int
    quote: str
    excerpt: str
