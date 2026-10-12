"""Immutable evidence accepted by the PDF process supervisor."""

from dataclasses import dataclass

from .pdf_page import PdfPage
from .pdf_worker_outcome import PdfWorkerOutcome


@dataclass(frozen=True)
class PdfWorkerResult:
    """Retain physical pages only after independent response validation."""

    outcome: PdfWorkerOutcome
    source_sha256: str
    pages: tuple[PdfPage, ...]
    total_pages: int | None
    missing_pages: tuple[int, ...]
