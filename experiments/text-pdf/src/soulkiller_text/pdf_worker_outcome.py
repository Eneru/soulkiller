"""Typed PDF adapter and observed supervision outcomes."""

from enum import StrEnum


class PdfWorkerOutcome(StrEnum):
    """Keep PDF evidence separate from worker guard and transport failures."""

    SUCCESS = "success"
    NO_TEXT = "no_text"
    ENCRYPTED_PDF = "encrypted_pdf"
    MALFORMED_INPUT = "malformed_input"
    PAGE_LIMIT = "page_limit"
    PARTIAL = "partial"
    UNSUPPORTED_DEPENDENCY = "unsupported_dependency"
    CANDIDATE_FAILURE = "candidate_failure"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    OUTPUT_LIMIT = "output_limit"
    PROTOCOL_ERROR = "protocol_error"
    UNSUPPORTED_ENVIRONMENT = "unsupported_environment"
