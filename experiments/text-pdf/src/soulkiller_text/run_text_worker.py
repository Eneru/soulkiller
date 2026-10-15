"""Public fixed-worker entry for immutable synthetic TXT byte snapshots."""

import sys
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

from .supervise import run_command, validate_source
from .worker_execution import WorkerExecution
from .worker_limits import WorkerLimits
from .worker_outcome import WorkerOutcome
from .worker_output_counter import WorkerOutputCounter
from .worker_result import WorkerResult


def _run_text_worker(
    source: bytes,
    limits: WorkerLimits | None,
    output_observer: Callable[[int], None] | None,
) -> WorkerResult:
    """Run the existing decoder under process guards; this API does not isolate networking."""
    validate_source(source)
    limits = WorkerLimits() if limits is None else limits
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    if sys.platform != "linux":
        return WorkerResult(WorkerOutcome.UNSUPPORTED_ENVIRONMENT, sha256(source).hexdigest(), None)
    command = (
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).with_name("worker_bootstrap.py").absolute()),
        str(limits.address_space_bytes),
    )
    if output_observer is None:
        return run_command(command, source, limits)
    return run_command(command, source, limits, output_observer=output_observer)


def run_text_worker(source: bytes, limits: WorkerLimits | None = None) -> WorkerResult:
    """Run the fixed TXT decoder while retaining the established public result API."""
    return _run_text_worker(source, limits, None)


def run_observed_text_worker(
    source: bytes, limits: WorkerLimits | None = None
) -> WorkerExecution[WorkerResult]:
    """Return a completed TXT result with actual combined transport consumption."""
    counter = WorkerOutputCounter()
    result = _run_text_worker(source, limits, counter.observe)
    return WorkerExecution(result, counter.output_bytes)
