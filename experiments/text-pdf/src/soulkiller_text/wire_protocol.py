"""Strict JSON for bounded worker responses; never deserialize executable data."""

import json
from typing import Literal, cast

from .worker_constants import MAX_OUTPUT_BYTES
from .worker_result import WorkerResult

type LiteralOutcome = Literal["success", "no_text", "invalid_encoding", "resource_limit"]


def encode_result(result: WorkerResult) -> bytes:
    """Encode only protocol values, preserving text without normalization."""
    return json.dumps(
        {
            "version": 1,
            "outcome": result.outcome,
            "source_sha256": result.source_sha256,
            "text": result.text,
        },
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")


def _unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
    fields: dict[str, object] = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("invalid_worker_response")
        fields[key] = value
    return fields


def _reject_constant(value: str) -> object:
    raise ValueError("invalid_worker_response")


def decode_result(payload: bytes, source_sha256: str) -> WorkerResult:
    """Verify the complete schema, original source revision and text invariants."""
    if len(payload) > MAX_OUTPUT_BYTES:
        raise ValueError("invalid_worker_response")
    try:
        fields = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_fields,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise ValueError("invalid_worker_response") from None
    if not isinstance(fields, dict) or set(fields) != {
        "version",
        "outcome",
        "source_sha256",
        "text",
    }:
        raise ValueError("invalid_worker_response")
    if type(fields["version"]) is not int or fields["version"] != 1:
        raise ValueError("invalid_worker_response")
    if fields["source_sha256"] != source_sha256:
        raise ValueError("invalid_worker_response")
    outcome = fields["outcome"]
    if outcome not in ("success", "no_text", "invalid_encoding", "resource_limit"):
        raise ValueError("invalid_worker_response")
    text = fields["text"]
    if outcome == "success":
        if (
            not isinstance(text, str)
            or not text
            or any(0xD800 <= ord(character) <= 0xDFFF for character in text)
        ):
            raise ValueError("invalid_worker_response")
    elif text is not None:
        raise ValueError("invalid_worker_response")
    return WorkerResult(cast("LiteralOutcome", outcome), source_sha256, cast("str | None", text))
