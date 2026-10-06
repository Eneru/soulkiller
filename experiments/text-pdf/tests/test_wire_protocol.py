"""Strict independent response records for the worker protocol."""

import json

import pytest

from soulkiller_text.wire_protocol import decode_result, encode_result
from soulkiller_text.worker_result import WorkerResult

from .synthetic_sources import BILINGUAL_SHA256, BILINGUAL_TEXT, EMPTY_SHA256, INVALID_SHA256
from .worker_fixtures import result_payload


def test_encoder_emits_exact_versioned_ascii_record() -> None:
    # Arrange
    result = WorkerResult("success", BILINGUAL_SHA256, BILINGUAL_TEXT)
    # Act
    payload = encode_result(result)
    # Assert
    assert payload.isascii()
    assert json.loads(payload) == {
        "version": 1,
        "outcome": "success",
        "source_sha256": BILINGUAL_SHA256,
        "text": BILINGUAL_TEXT,
    }


def test_decoder_preserves_unicode_line_endings_and_hash() -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256, text=BILINGUAL_TEXT)
    # Act
    result = decode_result(payload, BILINGUAL_SHA256)
    # Assert
    assert result == WorkerResult("success", BILINGUAL_SHA256, BILINGUAL_TEXT)


@pytest.mark.parametrize(
    ("outcome", "source_hash"),
    [
        ("no_text", EMPTY_SHA256),
        ("invalid_encoding", INVALID_SHA256),
        ("resource_limit", BILINGUAL_SHA256),
    ],
)
def test_supported_non_success_records_contain_no_text(outcome: str, source_hash: str) -> None:
    # Arrange
    payload = result_payload(source_hash, outcome, None)
    # Act
    result = decode_result(payload, source_hash)
    # Assert
    assert result.outcome == outcome
    assert result.source_sha256 == source_hash
    assert result.text is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", True),
        ("version", 2),
        ("version", 1.0),
        ("outcome", "timeout"),
        ("outcome", "unexpected"),
        ("outcome", None),
        ("source_sha256", "0" * 64),
        ("source_sha256", BILINGUAL_SHA256.upper()),
        ("source_sha256", None),
        ("text", ""),
        ("text", None),
        ("text", 1),
        ("text", "\ud800"),
    ],
)
def test_inconsistent_response_fields_are_rejected(field: str, value: object) -> None:
    # Arrange
    record = json.loads(result_payload(BILINGUAL_SHA256))
    record[field] = value
    payload = json.dumps(record).encode("ascii")
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(payload, BILINGUAL_SHA256)


@pytest.mark.parametrize("outcome", ["no_text", "invalid_encoding", "resource_limit"])
def test_failed_response_cannot_include_partial_text(outcome: str) -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256, outcome, "not accepted")
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(payload, BILINGUAL_SHA256)


@pytest.mark.parametrize("field", ["version", "outcome", "source_sha256", "text"])
def test_missing_required_field_is_rejected(field: str) -> None:
    # Arrange
    record = json.loads(result_payload(BILINGUAL_SHA256))
    del record[field]
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


def test_unknown_field_is_rejected() -> None:
    # Arrange
    record = json.loads(result_payload(BILINGUAL_SHA256))
    record["traceback"] = "never exposed"
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not-json",
        b"[]",
        b"null",
        b"true",
        b"1",
        b"{}",
        b"\xff",
        b'{"version":1,"version":1}',
        b'{"version":NaN}',
        b'{"version":Infinity}',
        b'{"version":-Infinity}',
        b"[" * 2000,
    ],
)
def test_malformed_duplicate_or_nonfinite_payload_is_rejected(payload: bytes) -> None:
    # Arrange
    response = payload
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(response, BILINGUAL_SHA256)


def test_trailing_second_response_is_rejected() -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256) * 2
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(payload, BILINGUAL_SHA256)
