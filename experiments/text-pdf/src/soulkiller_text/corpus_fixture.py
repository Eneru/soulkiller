"""Explicit synthetic source metadata from a validated manifest."""

from dataclasses import dataclass
from typing import Literal

from .text_annotation import TextAnnotation


@dataclass(frozen=True)
class CorpusFixture:
    """Describe selected bytes without verifying an author's identity."""

    fixture_id: str
    path: str
    sha256: str
    format: Literal["txt"]
    language: Literal["fr", "en"]
    author_label: str
    subject_label: str
    outcome: Literal["success", "no_text", "invalid_encoding"]
    annotations: tuple[TextAnnotation, ...]
