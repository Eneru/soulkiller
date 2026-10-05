"""An immutable outcome from decoding supplied source bytes."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ExtractionResult:
    """Retain the original byte hash, outcome and unmodified decoded text."""

    outcome: Literal["success", "no_text", "invalid_encoding"]
    source_sha256: str
    text: str | None
