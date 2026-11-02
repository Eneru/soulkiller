"""Bounded strict metadata JSON for saved manual extraction runs."""

import json
from typing import Never

from .fixture_record_constants import MAX_PAYLOAD_BYTES

INVALID_SAVED_RUN = "invalid_saved_run"


def _unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject repeated metadata keys instead of accepting hidden replacements."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(INVALID_SAVED_RUN)
        result[key] = value
    return result


def _reject(value: str) -> Never:
    """Metadata has no floats or nonfinite numbers; reject both token classes."""
    raise ValueError(INVALID_SAVED_RUN)


def encode_saved(value: object) -> bytes:
    """Encode compact metadata within the existing framed-record byte ceiling."""
    payload = json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
    if len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError(INVALID_SAVED_RUN)
    return payload


def decode_saved(payload: bytes) -> dict[str, object]:
    """Read bounded non-executable JSON with exact object and integer syntax."""
    if type(payload) is not bytes or len(payload) > MAX_PAYLOAD_BYTES:
        raise ValueError(INVALID_SAVED_RUN)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_float=_reject,
            parse_constant=_reject,
        )
    except (ValueError, RecursionError):
        raise ValueError(INVALID_SAVED_RUN) from None
    if type(value) is not dict:
        raise ValueError(INVALID_SAVED_RUN)
    return value
