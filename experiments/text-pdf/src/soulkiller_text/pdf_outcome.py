"""Named native PDF adapter outcomes, separate from TXT worker transport."""

from enum import StrEnum


class PdfOutcome(StrEnum):
    """Describe covered native text without claiming a complete evaluation run."""

    SUCCESS = "success"
    NO_TEXT = "no_text"
    ENCRYPTED_PDF = "encrypted_pdf"
    MALFORMED_INPUT = "malformed_input"
    PAGE_LIMIT = "page_limit"
    PARTIAL = "partial"
    UNSUPPORTED_DEPENDENCY = "unsupported_dependency"
    CANDIDATE_FAILURE = "candidate_failure"
