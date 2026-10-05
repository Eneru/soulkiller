"""Pure text extraction and evidence helpers for the evaluation experiment."""

from .evidence_slice import evidence_slice
from .extract_utf8 import extract_utf8
from .extraction_result import ExtractionResult
from .text_evidence import TextEvidence

__all__ = ["ExtractionResult", "TextEvidence", "evidence_slice", "extract_utf8"]
