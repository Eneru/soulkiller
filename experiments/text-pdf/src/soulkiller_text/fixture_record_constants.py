"""Exact schema fields and storage-compatible bounds for persisted fixture rows."""

from .run_store_constants import HEADER_BYTES, MAX_RECORD_BYTES
from .worker_constants import MAX_OUTPUT_BYTES

SCHEMA_VERSION = 1
MAX_PAYLOAD_BYTES = MAX_RECORD_BYTES - HEADER_BYTES
MAX_OBSERVED_OUTPUT_BYTES = MAX_OUTPUT_BYTES + 1
INVALID_RECORD = "invalid_fixture_record"
RECORD_TOO_LARGE = "fixture_record_too_large"
RECORD_FIELDS = frozenset(
    {
        "schema_version",
        "fixture_id",
        "format",
        "source_sha256",
        "result",
        "output_bytes",
        "unfinished_reason",
    }
)
TXT_RESULT_FIELDS = frozenset({"outcome", "text"})
PDF_RESULT_FIELDS = frozenset({"outcome", "pages", "total_pages", "missing_pages"})
