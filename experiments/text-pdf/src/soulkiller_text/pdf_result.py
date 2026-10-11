"""Immutable native PDF adapter record without protocol/authenticity claims."""

from dataclasses import dataclass

from .pdf_outcome import PdfOutcome
from .pdf_page import PdfPage


@dataclass(frozen=True)
class PdfResult:
    """Keep covered pages and known missing pages distinct from complete success."""

    outcome: PdfOutcome
    source_sha256: str
    pages: tuple[PdfPage, ...]
    total_pages: int | None
    missing_pages: tuple[int, ...]
