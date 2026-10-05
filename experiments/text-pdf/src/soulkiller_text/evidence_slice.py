"""Select exact evidence from a successful extraction result."""

from .extraction_result import ExtractionResult
from .text_evidence import TextEvidence


def evidence_slice(result: ExtractionResult, start: int, end: int) -> TextEvidence:
    """Return an exact code-point slice of successfully decoded text.

    Raise TypeError for non-integer offsets, including booleans. Raise ValueError
    for non-success outcomes or empty, negative, reversed and out-of-range spans.
    """
    if result.outcome != "success" or result.text is None:
        raise ValueError("Evidence requires a successful extraction with decoded text.")

    if (
        isinstance(start, bool)
        or not isinstance(start, int)
        or isinstance(end, bool)
        or not isinstance(end, int)
    ):
        raise TypeError("Evidence offsets must be integers, excluding booleans.")

    if start < 0 or end > len(result.text) or start >= end:
        raise ValueError("Evidence must be a nonempty span within the decoded text.")

    return TextEvidence(result.source_sha256, start, end, result.text[start:end])
