"""Isolated script: establish the child guard before importing the TXT candidate."""

import os
import resource
import sys


def _configure_address_space(limit: int) -> bool:
    """Set and read back the address-space ceiling; never change the parent."""
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        return resource.getrlimit(resource.RLIMIT_AS) == (limit, limit)
    except (OSError, ValueError):
        return False


def main(arguments: list[str] | None = None) -> int:
    """Use reserved exits for unavailable enforcement or explicit allocation failure."""
    arguments = sys.argv[1:] if arguments is None else arguments
    if len(arguments) != 1:
        return 3
    try:
        address_space = int(arguments[0])
    except ValueError:
        return 3
    # Keep this bootstrap check before any import of the package or candidate.
    if not 64 * 1024 * 1024 <= address_space <= 2 * 1024 * 1024 * 1024:
        return 3
    if not _configure_address_space(address_space):
        return 3
    try:
        # Isolated mode ignores cwd/PYTHONPATH; add only this reviewed source tree.
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from soulkiller_text.worker_candidate import run_candidate

        return run_candidate()
    except MemoryError:
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
