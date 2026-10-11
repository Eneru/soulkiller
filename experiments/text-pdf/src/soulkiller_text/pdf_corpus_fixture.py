"""Explicit synthetic PDF source metadata from a validated manifest."""

from dataclasses import dataclass
from typing import Literal

from .pdf_fact_annotation import PdfFactAnnotation


@dataclass(frozen=True)
class PdfCorpusFixture:
    """Declare independent references without parsing sources or inferring identity."""

    fixture_id: str
    path: str
    sha256: str
    format: Literal["pdf"]
    language: Literal["fr", "en"]
    author_label: str
    subject_label: str
    outcome: Literal["success", "no_text", "encrypted_pdf", "malformed_input"]
    annotations: tuple[PdfFactAnnotation, ...]
    page_count: int
