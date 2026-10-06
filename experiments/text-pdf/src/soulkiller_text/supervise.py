"""Own one trusted worker session, its bounded pipes and mandatory cleanup."""

import os
import signal
import subprocess
from hashlib import sha256
from time import monotonic, sleep

from .corpus_constants import MAX_SOURCE_BYTES
from .wire_protocol import decode_result
from .worker_cleanup_error import WorkerCleanupError
from .worker_constants import CLEANUP_SECONDS, MEMORY_FAILURE_EXIT, UNSUPPORTED_EXIT
from .worker_limits import WorkerLimits
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


def run_command(command: tuple[str, ...], source: bytes, limits: WorkerLimits) -> WorkerResult:
    """Internal trusted-command test seam; the public API selects one fixed worker."""
    validate_source(source)
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    source_hash = sha256(source).hexdigest()
    if not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT"):
        return WorkerResult("unsupported_environment", source_hash, None)
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
        return WorkerResult("candidate_failure", source_hash, None)
    try:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            return WorkerResult("candidate_failure", source_hash, None)
        failure, response = capture_pipes(
            process.stdin, process.stdout, process.stderr, source, deadline, limits.output_bytes
        )
        if failure in ("timeout", "output_limit"):
            return WorkerResult(failure, source_hash, None)
        remaining = deadline - monotonic()
        if remaining <= 0:
            return WorkerResult("timeout", source_hash, None)
        return_code = _wait_for_exit(process.pid, deadline)
        if return_code is None:
            return WorkerResult("timeout", source_hash, None)
        if return_code == UNSUPPORTED_EXIT:
            return WorkerResult("unsupported_environment", source_hash, None)
        if return_code == MEMORY_FAILURE_EXIT:
            return WorkerResult("resource_limit", source_hash, None)
        if return_code != 0 or failure == "candidate_failure":
            return WorkerResult("candidate_failure", source_hash, None)
        try:
            return decode_result(response, source_hash)
        except ValueError:
            return WorkerResult("protocol_error", source_hash, None)
    except OSError:
        return WorkerResult("candidate_failure", source_hash, None)
    finally:
        _cleanup(process)
