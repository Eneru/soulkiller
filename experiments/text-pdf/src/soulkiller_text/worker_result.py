"""An immutable supervised decoding result."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class WorkerResult:
    """Failed outcomes retain a source hash but never partial text or stderr."""

    outcome: Literal[
        "success",
        "no_text",
        "invalid_encoding",
        "timeout",
        "resource_limit",
        "output_limit",
        "candidate_failure",
        "protocol_error",
        "unsupported_environment",
    ]
    source_sha256: str
    text: str | None
