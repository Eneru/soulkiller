"""Isolated script: establish the child guard before importing the TXT candidate."""

import os
import sys

# This script runs before package imports; keep guard definitions standalone.
MIN_ADDRESS_SPACE_BYTES = 64 * 1024 * 1024
MAX_ADDRESS_SPACE_BYTES = 2 * 1024 * 1024 * 1024
UNSUPPORTED_EXIT = 3
MEMORY_FAILURE_EXIT = 4


def _configure_address_space(limit: int) -> bool:
    """Set and read back the address-space ceiling; never change the parent."""
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        return resource.getrlimit(resource.RLIMIT_AS) == (limit, limit)
    except (ImportError, OSError, ValueError):
        return False


def main(arguments: list[str] | None = None) -> int:
    """Use reserved exits for unavailable enforcement or explicit allocation failure."""
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) != 1:
        return UNSUPPORTED_EXIT
    try:
        address_space = int(arguments[0])
    except ValueError:
        return UNSUPPORTED_EXIT
    # Keep this bootstrap check before any import of the package or candidate.
    if not MIN_ADDRESS_SPACE_BYTES <= address_space <= MAX_ADDRESS_SPACE_BYTES:
        return UNSUPPORTED_EXIT
    if not _configure_address_space(address_space):
        return UNSUPPORTED_EXIT
    try:
        # Isolated mode ignores cwd/PYTHONPATH; add only this reviewed source tree.
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from soulkiller_text.worker_candidate import run_candidate

        return run_candidate()
    except MemoryError:
        return MEMORY_FAILURE_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
