"""Strict bounded JSON framing and PDF response scalar fields."""

import json
from typing import cast

from .pdf_outcome import PdfOutcome
from .pdf_worker_outcome import PdfWorkerOutcome
from .worker_constants import MAX_OUTPUT_BYTES

RESPONSE_FIELDS = frozenset(
    {"version", "outcome", "source_sha256", "pages", "total_pages", "missing_pages"}
)


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields: dict[str, object] = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("invalid_worker_response")
        fields[key] = value
    return fields


def _reject_constant(value: str) -> object:
    raise ValueError("invalid_worker_response")


def read_fields(payload: bytes, source_sha256: str) -> dict[str, object]:
    """Reject malformed framing, extra fields, versions and source revisions."""
    if type(payload) is not bytes or len(payload) > MAX_OUTPUT_BYTES:
        raise ValueError("invalid_worker_response")
    try:
        fields = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_fields,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise ValueError("invalid_worker_response") from None
    if not isinstance(fields, dict) or set(fields) != RESPONSE_FIELDS:
        raise ValueError("invalid_worker_response")
    if type(fields["version"]) is not int or fields["version"] != 2:
        raise ValueError("invalid_worker_response")
    source_hash = fields["source_sha256"]
    if (
        not isinstance(source_hash, str)
        or source_hash != source_sha256
        or len(source_hash) != 64
        or any(character not in "0123456789abcdef" for character in source_hash)
    ):
        raise ValueError("invalid_worker_response")
    return cast("dict[str, object]", fields)


def decode_outcome(value: object) -> PdfWorkerOutcome:
    """Candidate wire values cannot claim observed supervisor failures."""
    if not isinstance(value, str):
        raise ValueError("invalid_worker_response")
    try:
        candidate = PdfOutcome(value)
    except ValueError:
        raise ValueError("invalid_worker_response") from None
    return PdfWorkerOutcome(candidate.value)
