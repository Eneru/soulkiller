"""Own one trusted worker session, its bounded pipes and mandatory cleanup."""

import os
import signal
import subprocess
from collections.abc import Callable
from hashlib import sha256
from time import monotonic, sleep
from typing import overload

from .corpus_constants import MAX_SOURCE_BYTES
from .worker_cleanup_error import WorkerCleanupError
from .worker_completion import classify_completion
from .worker_completion_type import CompletionClassifier
from .worker_constants import CLEANUP_SECONDS, UNSUPPORTED_EXIT
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


def _complete_result[T](
    process_id: int,
    pipe_failure: WorkerOutcome | None,
    response: bytes,
    deadline: float,
    source_sha256: str,
    completion_classifier: CompletionClassifier[T],
) -> T:
    """Observe bounded exit only while its result can still meet the deadline."""
    return_code = None
    if pipe_failure not in (WorkerOutcome.TIMEOUT, WorkerOutcome.OUTPUT_LIMIT):
        if monotonic() < deadline:
            return_code = _wait_for_exit(process_id, deadline)
    return completion_classifier(return_code, pipe_failure, response, source_sha256)


def _capture_result[T](
    process: subprocess.Popen[bytes],
    source: bytes,
    limits: WorkerLimits,
    deadline: float,
    source_sha256: str,
    completion_classifier: CompletionClassifier[T],
    output_observer: Callable[[int], None] | None,
) -> T:
    """Transfer the snapshot, then delegate only completion interpretation."""
    if process.stdin is None or process.stdout is None or process.stderr is None:
        return completion_classifier(-1, WorkerOutcome.CANDIDATE_FAILURE, b"", source_sha256)
    if output_observer is None:
        failure, response = capture_pipes(
            process.stdin, process.stdout, process.stderr, source, deadline, limits.output_bytes
        )
    else:
        failure, response = capture_pipes(
            process.stdin,
            process.stdout,
            process.stderr,
            source,
            deadline,
            limits.output_bytes,
            output_observer=output_observer,
        )
    return _complete_result(
        process.pid, failure, response, deadline, source_sha256, completion_classifier
    )


@overload
def run_command(command: tuple[str, ...], source: bytes, limits: WorkerLimits) -> WorkerResult: ...


@overload
def run_command(
    command: tuple[str, ...],
    source: bytes,
    limits: WorkerLimits,
    *,
    output_observer: Callable[[int], None] | None,
) -> WorkerResult: ...


@overload
def run_command[T](
    command: tuple[str, ...],
    source: bytes,
    limits: WorkerLimits,
    completion_classifier: CompletionClassifier[T],
) -> T: ...


@overload
def run_command[T](
    command: tuple[str, ...],
    source: bytes,
    limits: WorkerLimits,
    completion_classifier: CompletionClassifier[T],
    *,
    output_observer: Callable[[int], None] | None,
) -> T: ...


def run_command[T](
    command: tuple[str, ...],
    source: bytes,
    limits: WorkerLimits,
    completion_classifier: CompletionClassifier[T | WorkerResult] = (classify_completion),
    *,
    output_observer: Callable[[int], None] | None = None,
) -> T | WorkerResult:
    """Own the reviewed process lifecycle and delegate format-specific completion."""
    validate_source(source)
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    source_hash = sha256(source).hexdigest()
    if not hasattr(os, "waitid") or not hasattr(os, "WNOWAIT"):
        return completion_classifier(UNSUPPORTED_EXIT, None, b"", source_hash)
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
        return completion_classifier(-1, WorkerOutcome.CANDIDATE_FAILURE, b"", source_hash)
    try:
        return _capture_result(
            process, source, limits, deadline, source_hash, completion_classifier, output_observer
        )
    except OSError:
        return completion_classifier(-1, WorkerOutcome.CANDIDATE_FAILURE, b"", source_hash)
    finally:
        _cleanup(process)
