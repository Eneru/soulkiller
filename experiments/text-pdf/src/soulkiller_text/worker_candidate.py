"""The trusted child-side UTF-8 baseline, with no path or network operations."""

import sys

from .corpus_constants import MAX_SOURCE_BYTES
from .extract_utf8 import extract_utf8
from .wire_protocol import encode_result
from .worker_result import WorkerResult


def run_candidate() -> int:
    """Read one bounded snapshot and write one exact, versioned JSON response."""
    source = sys.stdin.buffer.read(MAX_SOURCE_BYTES + 1)
    if len(source) > MAX_SOURCE_BYTES:
        return 2
    result = extract_utf8(source)
    payload = encode_result(WorkerResult(result.outcome, result.source_sha256, result.text))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    return 0
