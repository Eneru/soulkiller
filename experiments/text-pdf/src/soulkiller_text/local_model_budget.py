"""Linux-only resource guards for the manually launched inference container."""

import signal
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import FrameType

from .dialogue_error import DialogueError
from .local_model_constants import MAX_SECONDS, MEMORY_BYTES, THREADS
from .worker_network_guard import has_offline_topology


def require_local_budget() -> None:
    """Require loopback-only topology and the declared cgroup v2 upper bounds."""
    root = Path("/sys/fs/cgroup")
    try:
        memory = int((root / "memory.max").read_text().strip())
        quota, period = map(int, (root / "cpu.max").read_text().split())
    except (OSError, ValueError):
        raise DialogueError("local_model_container_limits_required") from None
    if not has_offline_topology() or not (
        0 < memory <= MEMORY_BYTES and 0 < quota <= THREADS * period
    ):
        raise DialogueError("local_model_container_limits_required")


def _timeout(_number: int, _frame: FrameType | None) -> None:
    """Interrupt blocking I/O even if a peer sends bytes below socket timeout intervals."""
    raise DialogueError("local_model_timeout")


@contextmanager
def local_deadline(seconds: int | None = None) -> Iterator[None]:
    """Use Linux's process-wide timer for the single foreground CLI; restore on exit."""
    duration = MAX_SECONDS if seconds is None else seconds
    if seconds is not None and (type(seconds) is not int or not 0 < seconds <= MAX_SECONDS):
        raise DialogueError("local_model_deadline_unavailable")
    try:
        if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
            raise DialogueError("local_model_deadline_unavailable")
        previous = signal.signal(signal.SIGALRM, _timeout)
    except ValueError:
        raise DialogueError("local_model_deadline_unavailable") from None
    try:
        signal.setitimer(signal.ITIMER_REAL, duration)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
