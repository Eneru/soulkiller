"""Independent reference quotes attributed to physical PDF pages."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PdfFactAnnotation:
    """Reference metadata; loading does not verify extraction or reading order."""

    page_number: int
    quote: str
