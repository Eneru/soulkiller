"""Fixed framing, naming and encoded-byte ceilings for opaque run storage."""

from .corpus_constants import MAX_FIXTURES
from .run_constants import MAX_RUN_OUTPUT_BYTES
from .worker_constants import MAX_OUTPUT_BYTES

OUTPUT_PARTS = (".soulkiller-local", "evaluation")
NAME_PATTERN = r"[a-z0-9][a-z0-9_-]{0,63}"
MAGIC = b"SKRUN01\n"
LENGTH_BYTES = 8
DIGEST_BYTES = 32
HEADER_BYTES = len(MAGIC) + LENGTH_BYTES + DIGEST_BYTES
MAX_RECORD_BYTES = MAX_OUTPUT_BYTES
MAX_STORE_BYTES = MAX_RUN_OUTPUT_BYTES
MAX_RECORDS = MAX_FIXTURES + 2
DIRECTORY_MODE = 0o700
FILE_MODE = 0o600
SCRATCH_PREFIX = ".scratch-"
SCRATCH_TOKEN_BYTES = 16

INVALID_NAME = "invalid_name"
INVALID_PAYLOAD = "invalid_payload"
INVALID_PATH = "invalid_path"
UNSUPPORTED_PLATFORM = "unsupported_platform"
SOURCE_OVERLAP = "source_overlap"
UNSAFE_PATH = "unsafe_path"
SOURCE_UNAVAILABLE = "source_unavailable"
RUN_EXISTS = "run_exists"
RECORD_EXISTS = "record_exists"
STORAGE_UNAVAILABLE = "storage_unavailable"
RECORD_TOO_LARGE = "record_too_large"
STORE_LIMIT = "store_limit"
RECORD_LIMIT = "record_limit"
INVALID_RECORD = "invalid_record"
RECORD_UNAVAILABLE = "record_unavailable"
READ_ONLY = "read_only"
CLOSED = "closed"
WRITE_FAILED = "write_failed"
