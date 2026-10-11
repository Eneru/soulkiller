"""One physical source page's unchanged candidate text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfPage:
    """Page numbers are one-based; text offsets are code points, not coordinates."""

    page_number: int
    text: str
