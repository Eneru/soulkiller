"""Reviewed per-worker ceilings and internal transfer constants."""

from .worker_bootstrap import (
    MAX_ADDRESS_SPACE_BYTES as MAX_ADDRESS_SPACE_BYTES,
)
from .worker_bootstrap import (
    MEMORY_FAILURE_EXIT as MEMORY_FAILURE_EXIT,
)
from .worker_bootstrap import (
    MIN_ADDRESS_SPACE_BYTES as MIN_ADDRESS_SPACE_BYTES,
)
from .worker_bootstrap import (
    UNSUPPORTED_EXIT as UNSUPPORTED_EXIT,
)

MAX_WALL_SECONDS = 60.0
MAX_OUTPUT_BYTES = 10 * 1024 * 1024
PIPE_CHUNK_BYTES = 64 * 1024
CLEANUP_SECONDS = 2.0
SUCCESS_EXIT = 0
INPUT_FAILURE_EXIT = 2
