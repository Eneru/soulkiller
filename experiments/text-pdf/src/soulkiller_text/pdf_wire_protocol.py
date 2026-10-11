"""Strict PDF version-2 JSON; encoded values never replace parent validation."""

import json

from .pdf_constants import MAX_PDF_PAGES
from .pdf_response_evidence import decode_count, decode_missing, decode_pages, validate_evidence
from .pdf_response_fields import decode_outcome, read_fields
from .pdf_result import PdfResult
from .pdf_worker_result import PdfWorkerResult


def encode_result(result: PdfResult | PdfWorkerResult) -> bytes:
    """Serialize adapter or verified worker records without changing physical text."""
    return json.dumps(
        {
            "version": 2,
            "outcome": result.outcome.value,
            "source_sha256": result.source_sha256,
            "pages": [
                {"page_number": page.page_number, "text": page.text} for page in result.pages
            ],
            "total_pages": result.total_pages,
            "missing_pages": list(result.missing_pages),
        },
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def decode_result(
    payload: bytes, source_sha256: str, max_pages: int = MAX_PDF_PAGES
) -> PdfWorkerResult:
    """Independently verify fields, revision, page bounds and outcome coverage."""
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PDF_PAGES:
        raise ValueError("invalid_worker_response")
    fields = read_fields(payload, source_sha256)
    outcome = decode_outcome(fields["outcome"])
    pages = decode_pages(fields["pages"], max_pages)
    total = decode_count(fields["total_pages"])
    missing = decode_missing(fields["missing_pages"], max_pages)
    validate_evidence(outcome, pages, total, missing, max_pages)
    return PdfWorkerResult(outcome, source_sha256, pages, total, missing)
