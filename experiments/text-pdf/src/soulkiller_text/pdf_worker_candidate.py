"""The guarded native PDF candidate, accepting one bounded immutable snapshot."""

import sys

from .corpus_constants import MAX_SOURCE_BYTES
from .native_pdf import extract_native_pdf
from .pdf_wire_protocol import encode_result
from .worker_constants import INPUT_FAILURE_EXIT, SUCCESS_EXIT


def run_candidate(max_pages: int) -> int:
    """Parse bounded bytes after bootstrap guards and emit only structured evidence."""
    source = sys.stdin.buffer.read(MAX_SOURCE_BYTES + 1)
    if len(source) > MAX_SOURCE_BYTES:
        return INPUT_FAILURE_EXIT
    payload = encode_result(extract_native_pdf(source, max_pages))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    return SUCCESS_EXIT
