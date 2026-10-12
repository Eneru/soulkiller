"""Standalone PDF entry: verify inherited guards before package/parser imports."""

import os
import sys
from typing import TYPE_CHECKING

# Fallback exits must remain available when standalone guard imports fail.
FALLBACK_UNSUPPORTED_EXIT = 3
FALLBACK_MEMORY_FAILURE_EXIT = 4


def _configure_guards(address_space: int) -> bool:
    """Reuse the reviewed memory guard and verify the externally offline topology."""
    if TYPE_CHECKING:
        from . import worker_bootstrap, worker_network_guard
    else:
        import worker_bootstrap
        import worker_network_guard

    return (
        worker_bootstrap._configure_address_space(address_space)
        and worker_network_guard.has_offline_topology()
    )


def _run_guarded(arguments: list[str]) -> int:
    """Load reviewed standalone helpers, validate arguments and apply both guards."""
    # Isolated mode ignores cwd/PYTHONPATH; load only reviewed standalone helpers.
    source_directory = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, source_directory)
    try:
        if TYPE_CHECKING:
            from . import pdf_constants, worker_bootstrap
        else:
            import pdf_constants
            import worker_bootstrap

        if len(arguments) != 2:
            return worker_bootstrap.UNSUPPORTED_EXIT
        try:
            address_space, max_pages = (int(value) for value in arguments)
        except ValueError:
            return worker_bootstrap.UNSUPPORTED_EXIT
        if (
            not worker_bootstrap.MIN_ADDRESS_SPACE_BYTES
            <= (address_space)
            <= worker_bootstrap.MAX_ADDRESS_SPACE_BYTES
        ):
            return worker_bootstrap.UNSUPPORTED_EXIT
        if not 1 <= max_pages <= pdf_constants.MAX_PDF_PAGES:
            return worker_bootstrap.UNSUPPORTED_EXIT
        if not _configure_guards(address_space):
            return worker_bootstrap.UNSUPPORTED_EXIT
    except ImportError:
        return FALLBACK_UNSUPPORTED_EXIT
    # The package and candidate may load only after memory/network enforcement.
    sys.path.insert(0, os.path.dirname(source_directory))
    from soulkiller_text.pdf_worker_candidate import run_candidate

    return run_candidate(max_pages)


def main(arguments: list[str] | None = None) -> int:
    """Contain guard-import/allocation failures without requiring imports to succeed."""
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        return _run_guarded(arguments)
    except MemoryError:
        return FALLBACK_MEMORY_FAILURE_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
