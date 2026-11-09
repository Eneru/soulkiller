"""Bounded JSON transport for the fixed loopback server."""

import json
from http.client import HTTPConnection, HTTPException
from typing import Any

from .dialogue_constants import MAX_COMPLETION_BYTES
from .dialogue_error import DialogueError
from .local_model_constants import MAX_SECONDS, SERVER_HOST, SERVER_PORT


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous server fields before interpreting the response."""
    fields: dict[str, Any] = {}
    for key, value in pairs:
        if key in fields:
            raise ValueError("duplicate_field")
        fields[key] = value
    return fields


def _reject_constant(_value: str) -> None:
    """Disallow non-JSON numeric literals in server envelopes."""
    raise ValueError("invalid_number")


def server_request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Read a single bounded object without redirects, proxies, or decompression.

    Only a refused/loading health probe is retryable. The caller supplies
    fixed paths and an overall process timer.
    """
    connection = HTTPConnection(SERVER_HOST, SERVER_PORT, timeout=MAX_SECONDS)
    try:
        body = None if payload is None else json.dumps(payload, allow_nan=False)
        connection.request(
            "GET" if body is None else "POST", path, body, {"Content-Type": "application/json"}
        )
        with connection.getresponse() as response:
            if path == "/health" and response.status == 503:
                return None
            if (
                response.status != 200
                or response.getheader("Content-Encoding") is not None
                or response.getheader("Transfer-Encoding") is not None
                or response.headers.get_content_type() != "application/json"
            ):
                raise DialogueError("local_model_http_rejected")
            lengths = response.headers.get_all("Content-Length", [])
            if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                raise DialogueError("local_model_http_rejected")
            if len(lengths[0]) > len(str(MAX_COMPLETION_BYTES)):
                raise DialogueError("local_model_response_too_large")
            size = int(lengths[0])
            if size > MAX_COMPLETION_BYTES:
                raise DialogueError("local_model_response_too_large")
            raw = response.read(size)
            if len(raw) != size:
                raise DialogueError("local_model_transport_error")
    except ConnectionRefusedError:
        if path == "/health":
            return None
        raise DialogueError("local_model_transport_error") from None
    except (OSError, HTTPException):
        raise DialogueError("local_model_transport_error") from None
    finally:
        connection.close()
    try:
        fields = json.loads(raw, object_pairs_hook=_unique_fields, parse_constant=_reject_constant)
    except (ValueError, RecursionError):
        raise DialogueError("invalid_local_model_envelope") from None
    if type(fields) is not dict:
        raise DialogueError("invalid_local_model_envelope")
    return fields
