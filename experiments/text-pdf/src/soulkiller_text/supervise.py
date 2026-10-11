"""Own one trusted worker session, its bounded pipes and mandatory cleanup."""

import os
import signal
import subprocess
from hashlib import sha256
from time import monotonic, sleep

from .corpus_constants import MAX_SOURCE_BYTES
from .worker_cleanup_error import WorkerCleanupError
from .worker_completion import classify_completion
from .worker_constants import CLEANUP_SECONDS
from .worker_limits import WorkerLimits
from .worker_outcome import WorkerOutcome
from .worker_pipes import capture_pipes
from .worker_result import WorkerResult


def validate_source(source: bytes) -> None:
    """Reject mutable/non-byte inputs and oversized snapshots before launch."""
    if type(source) is not bytes:
        raise TypeError("invalid_worker_source")
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("worker_input_too_large")


def _cleanup(process: subprocess.Popen[bytes]) -> None:
    """Kill the owned group even after leader exit, close pipes and reap the leader."""
    failed = False
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError:
        failed = True
    for stream in (process.stdin, process.stdout, process.stderr):
        if stream is not None:
            try:
                stream.close()
            except OSError:
                failed = True
    try:
        process.wait(timeout=CLEANUP_SECONDS)
    except (OSError, subprocess.TimeoutExpired):
        failed = True
    if failed:
        raise WorkerCleanupError()


def _wait_for_exit(process_id: int, deadline: float) -> int | None:
    """Observe exit without reaping, keeping the group leader PID reserved."""
    while True:
        info = os.waitid(os.P_PID, process_id, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        if info is not None:
            return info.si_status if info.si_code == os.CLD_EXITED else -info.si_status
        remaining = deadline - monotonic()
        if remaining <= 0:
            return None
        sleep(min(remaining, 0.01))


def _complete_result(
    process_id: int,
    pipe_failure: WorkerOutcome | None,
    response: bytes,
    deadline: float,
    source_sha256: str,
) -> WorkerResult:
    """Observe bounded exit only while its result can still meet the deadline."""
    return_code = None
    if pipe_failure not in (WorkerOutcome.TIMEOUT, WorkerOutcome.OUTPUT_LIMIT):
        if monotonic() < deadline:
            return_code = _wait_for_exit(process_id, deadline)
    return classify_completion(return_code, pipe_failure, response, source_sha256)


def run_command(command: tuple[str, ...], source: bytes, limits: WorkerLimits) -> WorkerResult:
    """Internal trusted-command test seam; the public API selects one fixed worker."""
    validate_source(source)
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    source_hash = sha256(source).hexdigest()
    if not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT"):
        return WorkerResult(WorkerOutcome.UNSUPPORTED_ENVIRONMENT, source_hash, None)
    deadline = monotonic() + limits.wall_seconds
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            close_fds=True,
            start_new_session=True,
            env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
    except OSError:
        return WorkerResult(WorkerOutcome.CANDIDATE_FAILURE, source_hash, None)
    try:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            return WorkerResult(WorkerOutcome.CANDIDATE_FAILURE, source_hash, None)
        failure, response = capture_pipes(
            process.stdin, process.stdout, process.stderr, source, deadline, limits.output_bytes
        )
        return _complete_result(process.pid, failure, response, deadline, source_hash)
    except OSError:
        return WorkerResult(WorkerOutcome.CANDIDATE_FAILURE, source_hash, None)
    finally:
        _cleanup(process)
