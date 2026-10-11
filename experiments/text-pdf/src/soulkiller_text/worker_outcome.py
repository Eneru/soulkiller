"""Named public outcomes with stable string values for worker responses."""

from enum import StrEnum


class WorkerOutcome(StrEnum):
    """Keep typed worker results compatible with the documented JSON wire values."""

    SUCCESS = "success"
    NO_TEXT = "no_text"
    INVALID_ENCODING = "invalid_encoding"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    OUTPUT_LIMIT = "output_limit"
    CANDIDATE_FAILURE = "candidate_failure"
    PROTOCOL_ERROR = "protocol_error"
    UNSUPPORTED_ENVIRONMENT = "unsupported_environment"
