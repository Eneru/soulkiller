"""The child decoder consumes a bounded snapshot and emits only protocol data."""

import io
import json
import sys

import pytest

from soulkiller_text import worker_candidate

from .synthetic_sources import (
    BILINGUAL_BYTES,
    BILINGUAL_SHA256,
    BILINGUAL_TEXT,
    EMPTY_SHA256,
    INVALID_BYTES,
    INVALID_SHA256,
)


@pytest.mark.parametrize(
    ("source", "outcome", "text", "source_hash"),
    [
        (BILINGUAL_BYTES, "success", BILINGUAL_TEXT, BILINGUAL_SHA256),
        (b"", "no_text", None, EMPTY_SHA256),
        (INVALID_BYTES, "invalid_encoding", None, INVALID_SHA256),
    ],
)
def test_candidate_writes_independent_expected_record(
    monkeypatch: pytest.MonkeyPatch,
    source: bytes,
    outcome: str,
    text: str | None,
    source_hash: str,
) -> None:
    # Arrange
    input_buffer = io.BytesIO(source)
    output_buffer = io.BytesIO()
    stdin = io.TextIOWrapper(input_buffer)
    stdout = io.TextIOWrapper(output_buffer)
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    # Act
    exit_code = worker_candidate.run_candidate()
    # Assert
    assert exit_code == 0
    assert input_buffer.tell() == len(source)
    assert json.loads(output_buffer.getvalue()) == {
        "version": 1,
        "outcome": outcome,
        "source_sha256": source_hash,
        "text": text,
    }


def test_oversized_child_input_is_rejected_without_decoding_or_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    cap = 5 * 1024**2
    input_buffer = io.BytesIO(b"x" * (cap + 2))
    output_buffer = io.BytesIO()
    stdin = io.TextIOWrapper(input_buffer)
    stdout = io.TextIOWrapper(output_buffer)
    monkeypatch.setattr(sys, "stdin", stdin)
    monkeypatch.setattr(sys, "stdout", stdout)
    decoded: list[object] = []

    def forbidden(*args: object) -> None:
        decoded.append(args)
        raise AssertionError("Oversized child input must not be decoded.")

    monkeypatch.setattr(worker_candidate, "extract_utf8", forbidden)
    # Act
    exit_code = worker_candidate.run_candidate()
    # Assert
    assert exit_code == 2
    assert input_buffer.tell() == cap + 1
    assert output_buffer.getvalue() == b""
    assert decoded == []
