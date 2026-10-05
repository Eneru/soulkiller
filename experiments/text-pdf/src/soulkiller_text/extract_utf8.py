"""Decode bytes without normalization, filesystem access or network access."""

from hashlib import sha256

from .extraction_result import ExtractionResult


def extract_utf8(source: bytes) -> ExtractionResult:
    """Strictly decode UTF-8, retaining the SHA-256 of the original bytes."""
    source_sha256 = sha256(source).hexdigest()
    if not source:
        return ExtractionResult("no_text", source_sha256, None)

    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return ExtractionResult("invalid_encoding", source_sha256, None)

    return ExtractionResult("success", source_sha256, text)
