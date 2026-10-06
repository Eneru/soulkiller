"""Public fixed-worker entry for immutable synthetic TXT byte snapshots."""

import sys
from hashlib import sha256
from pathlib import Path

from .supervise import run_command, validate_source
from .worker_limits import WorkerLimits
from .worker_result import WorkerResult


def run_text_worker(source: bytes, limits: WorkerLimits | None = None) -> WorkerResult:
    """Run the existing decoder under process guards; this API does not isolate networking."""
    validate_source(source)
    limits = WorkerLimits() if limits is None else limits
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    if sys.platform != "linux":
        return WorkerResult("unsupported_environment", sha256(source).hexdigest(), None)
    command = (
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).with_name("worker_bootstrap.py").absolute()),
        str(limits.address_space_bytes),
    )
    return run_command(command, source, limits)
