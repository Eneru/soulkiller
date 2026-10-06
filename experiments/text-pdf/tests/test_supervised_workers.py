"""Actual synthetic child processes exercise bounded transfer and cleanup."""

from __future__ import annotations

import io
import os
import subprocess
import time
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import BinaryIO, Literal, cast

import pytest

from soulkiller_text import supervise
from soulkiller_text.supervise import run_command
from soulkiller_text.worker_cleanup_error import WorkerCleanupError
from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_pipes import capture_pipes

from .synthetic_sources import BILINGUAL_BYTES, BILINGUAL_SHA256
from .worker_fixtures import (
    blocking_command,
    flooding_command,
    inherited_pipe_command,
    memory_failure_command,
    responding_command,
    result_payload,
    worker_command,
)
from .worker_process_helpers import (
    assert_reaped,
    process_is_stopped,
    record_processes,
    stop_probe_process,
)


def test_verified_response_is_accepted_only_after_exit_and_pipe_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256, text="independent result")
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(responding_command(payload), BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "success"
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.text == "independent result"
    assert_reaped(processes)


def test_worker_not_reading_large_stdin_cannot_bypass_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    source = b"x" * (5 * 1024**2)
    processes = record_processes(monkeypatch)
    limits = WorkerLimits(wall_seconds=0.5)
    # Act
    result = run_command(blocking_command(), source, limits)
    # Assert
    assert result.outcome == "timeout"
    assert result.source_sha256 == sha256(source).hexdigest()
    assert result.text is None
    assert_reaped(processes)


@pytest.mark.parametrize("descriptor", [1, 2], ids=["stdout", "stderr"])
def test_flooding_each_output_stream_is_bounded_and_does_not_expose_text(
    monkeypatch: pytest.MonkeyPatch, descriptor: int
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)
    limits = WorkerLimits(wall_seconds=5, output_bytes=1024)
    # Act
    result = run_command(flooding_command(descriptor), BILINGUAL_BYTES, limits)
    # Assert
    assert result.outcome == "output_limit"
    assert result.text is None
    assert_reaped(processes)


@pytest.mark.parametrize("extra_byte", [False, True], ids=["exact-cap", "one-over"])
def test_stdout_and_stderr_share_one_byte_budget(extra_byte: bool) -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256)
    stderr = b"private diagnostic" + (b"!" if extra_byte else b"")
    limits = WorkerLimits(output_bytes=len(payload) + len(b"private diagnostic"))
    # Act
    result = run_command(responding_command(payload, stderr=stderr), BILINGUAL_BYTES, limits)
    # Assert
    assert result.outcome == ("output_limit" if extra_byte else "success")
    assert result.text == (None if extra_byte else "synthetic")
    assert "private diagnostic" not in repr(result)


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(b"not-json", id="malformed"),
        pytest.param(b'{"version":1,"version":1}', id="duplicate"),
        pytest.param(result_payload("0" * 64), id="wrong-source-hash"),
        pytest.param(result_payload(BILINGUAL_SHA256) * 2, id="extra-response"),
    ],
)
def test_invalid_response_never_promotes_text(payload: bytes) -> None:
    # Arrange
    command = responding_command(payload)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "protocol_error"
    assert result.text is None
    assert result.source_sha256 == BILINGUAL_SHA256


@pytest.mark.parametrize(
    ("exit_code", "expected"),
    [(1, "candidate_failure"), (3, "unsupported_environment"), (4, "resource_limit")],
)
def test_reserved_and_unexplained_nonzero_exits_have_explicit_outcomes(
    exit_code: int, expected: str
) -> None:
    # Arrange
    command = responding_command(result_payload(BILINGUAL_SHA256), exit_code=exit_code)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == expected
    assert result.text is None


def test_crash_signal_does_not_invent_a_memory_limit_cause() -> None:
    # Arrange
    command = worker_command("import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n")
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "candidate_failure"
    assert result.text is None


def test_actual_bounded_allocation_failure_is_visible_without_large_parent_allocation() -> None:
    # Arrange
    command = memory_failure_command(BILINGUAL_SHA256)
    limits = WorkerLimits(address_space_bytes=64 * 1024**2)
    # Act
    result = run_command(command, BILINGUAL_BYTES, limits)
    # Assert
    assert result.outcome == "resource_limit"
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.text is None


def test_worker_startup_failure_has_no_raw_error_or_source_text() -> None:
    # Arrange
    command = ("/definitely-not-a-soulkiller-executable",)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "candidate_failure"
    assert result.text is None
    assert "definitely-not" not in repr(result)


def test_valid_early_response_does_not_bypass_worker_exit_deadline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256)
    command = worker_command(
        "import os, time\n"
        f"os.write(1, {payload!r})\n"
        "os.close(0)\nos.close(1)\nos.close(2)\ntime.sleep(60)\n"
    )
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(wall_seconds=0.5))
    # Assert
    assert result.outcome == "timeout"
    assert result.text is None
    assert_reaped(processes)


def test_exited_leader_with_inherited_child_pipes_is_stopped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    child_pid_path = tmp_path / "synthetic-child.pid"
    processes = record_processes(monkeypatch)
    command = inherited_pipe_command(child_pid_path)
    # Act
    result = run_command(command, b"", WorkerLimits(wall_seconds=0.5))
    child_pid = int(child_pid_path.read_text(encoding="ascii"))
    deadline = time.monotonic() + 2
    while not process_is_stopped(child_pid) and time.monotonic() < deadline:
        time.sleep(0.01)
    # Assert
    assert result.outcome == "timeout"
    assert result.text is None
    assert_reaped(processes)
    assert process_is_stopped(child_pid)


def test_operator_cancellation_propagates_after_worker_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)

    def cancelled(*args: object) -> tuple[None, bytes]:
        raise KeyboardInterrupt()

    monkeypatch.setattr(supervise, "capture_pipes", cancelled)
    # Act
    with pytest.raises(KeyboardInterrupt):
        run_command(blocking_command(), BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert_reaped(processes)


def test_elapsed_launch_and_transfer_time_cannot_accept_an_early_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    clock = iter([0.0, 61.0])
    payload = result_payload(BILINGUAL_SHA256)
    monkeypatch.setattr(supervise, "monotonic", lambda: next(clock))
    monkeypatch.setattr(supervise, "capture_pipes", lambda *args: (None, payload))
    # Act
    result = run_command(blocking_command(), BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "timeout"
    assert result.text is None


def test_pipe_io_failure_still_cleans_up_and_returns_safe_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)

    def failed(*args: object) -> tuple[None, bytes]:
        raise OSError("sensitive synthetic diagnostic")

    monkeypatch.setattr(supervise, "capture_pipes", failed)
    # Act
    result = run_command(blocking_command(), BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "candidate_failure"
    assert "sensitive" not in repr(result)
    assert_reaped(processes)


def test_group_termination_failure_raises_distinct_safe_cleanup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)
    original_kill = os.killpg

    def failed_kill(pid: int, sig: int) -> None:
        raise PermissionError("private synthetic termination diagnostic")

    monkeypatch.setattr(os, "killpg", failed_kill)
    # Act
    try:
        with pytest.raises(WorkerCleanupError) as failure:
            run_command(
                responding_command(result_payload(BILINGUAL_SHA256)),
                BILINGUAL_BYTES,
                WorkerLimits(),
            )
    finally:
        monkeypatch.setattr(os, "killpg", original_kill)
        for process in processes:
            stop_probe_process(process)
    # Assert
    assert "private" not in str(failure.value)
    assert_reaped(processes)


def test_leader_reap_failure_raises_distinct_safe_cleanup_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    process_class = subprocess.Popen
    original_wait = process_class.wait
    processes = record_processes(monkeypatch)

    def failed_reap(process: subprocess.Popen[bytes], timeout: float | None = None) -> int:
        if timeout == 2:
            raise subprocess.TimeoutExpired("synthetic worker", timeout)
        return original_wait(process, timeout=timeout)

    monkeypatch.setattr(process_class, "wait", failed_reap)
    # Act
    try:
        with pytest.raises(WorkerCleanupError):
            run_command(
                responding_command(result_payload(BILINGUAL_SHA256)),
                BILINGUAL_BYTES,
                WorkerLimits(),
            )
    finally:
        for process in processes:
            original_wait(process, timeout=2)
    # Assert
    assert_reaped(processes)


@pytest.mark.parametrize("source", [bytearray(b"private"), memoryview(b"private"), "private", None])
def test_nonbyte_input_fails_before_spawn(source: object, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    spawned: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        spawned.append(args)
        raise AssertionError("Invalid input must not launch a worker.")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    # Act
    with pytest.raises(TypeError, match="^invalid_worker_source$"):
        run_command(blocking_command(), cast(bytes, source), WorkerLimits())
    # Assert
    assert spawned == []


def test_oversized_source_fails_before_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    source = b"x" * (5 * 1024**2 + 1)
    spawned: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        spawned.append(args)
        raise AssertionError("Oversized input must not launch a worker.")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    # Act
    with pytest.raises(ValueError, match="^worker_input_too_large$"):
        run_command(blocking_command(), source, WorkerLimits())
    # Assert
    assert spawned == []


def test_invalid_limits_object_fails_before_spawn(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    spawned: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        spawned.append(args)
        raise AssertionError("Invalid limits must not launch a worker.")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    # Act
    with pytest.raises(ValueError, match="^invalid_worker_limits$"):
        run_command(blocking_command(), BILINGUAL_BYTES, cast(WorkerLimits, object()))
    # Assert
    assert spawned == []


@pytest.mark.parametrize("capability", ["waitid", "WNOWAIT"])
def test_unavailable_pid_ownership_guard_prevents_launch(
    monkeypatch: pytest.MonkeyPatch,
    capability: str,
) -> None:
    # Arrange
    launched: list[object] = []

    def forbidden(*args: object, **kwargs: object) -> None:
        launched.append(args)
        raise AssertionError("Missing PID ownership guard must prevent launch.")

    monkeypatch.delattr(os, capability)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    # Act
    result = run_command(blocking_command(), BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "unsupported_environment"
    assert result.text is None
    assert launched == []


def test_leader_pid_is_reserved_until_group_cleanup_and_final_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    process_class = subprocess.Popen
    original_wait = process_class.wait
    original_kill = os.killpg
    processes = record_processes(monkeypatch)
    events: list[str] = []
    statuses_before_kill: list[int | None] = []

    def observed_kill(pid: int, sig: int) -> None:
        events.append("group-stop")
        statuses_before_kill.append(processes[0].returncode)
        original_kill(pid, sig)

    def observed_wait(process: subprocess.Popen[bytes], timeout: float | None = None) -> int:
        events.append("leader-reap")
        return original_wait(process, timeout=timeout)

    monkeypatch.setattr(os, "killpg", observed_kill)
    monkeypatch.setattr(process_class, "wait", observed_wait)
    # Act
    result = run_command(
        responding_command(result_payload(BILINGUAL_SHA256)),
        BILINGUAL_BYTES,
        WorkerLimits(),
    )
    # Assert
    assert result.outcome == "success"
    assert events == ["group-stop", "leader-reap"]
    assert statuses_before_kill == [None]
    assert_reaped(processes)


def test_inherited_private_and_loader_environment_is_absent_from_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    monkeypatch.setenv("SOULKILLER_TEST_SECRET", "private synthetic marker")
    monkeypatch.setenv("LD_LIBRARY_PATH", "/definitely-not-a-soulkiller-loader")
    command = worker_command(
        "import json, os, sys\n"
        "sys.stdin.buffer.read()\n"
        "text = ','.join(sorted(os.environ))\n"
        f"record = {{'version': 1, 'outcome': 'success', 'source_sha256': {BILINGUAL_SHA256!r}, "
        "'text': text}\n"
        "sys.stdout.buffer.write(json.dumps(record).encode('ascii'))\n"
    )
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits())
    # Assert
    assert result.outcome == "success"
    assert result.text == "LANG,LC_ALL"
    assert "private synthetic marker" not in repr(result)


@pytest.mark.parametrize("channel", ["read", "write"])
def test_nonblocking_pipe_retry_preserves_complete_response(
    monkeypatch: pytest.MonkeyPatch,
    channel: str,
) -> None:
    # Arrange
    original_capture = capture_pipes
    original_read = os.read
    original_write = os.write
    retried: list[str] = []

    def retry_read(descriptor: int, count: int) -> bytes:
        if not retried:
            retried.append("read")
            raise BlockingIOError()
        return original_read(descriptor, count)

    def retry_write(descriptor: int, source: bytes) -> int:
        if not retried:
            retried.append("write")
            raise BlockingIOError()
        return original_write(descriptor, source)

    def capture(
        stdin: BinaryIO,
        stdout: BinaryIO,
        stderr: BinaryIO,
        source: bytes,
        deadline: float,
        output_limit: int,
    ) -> tuple[Literal["timeout", "output_limit", "candidate_failure"] | None, bytes]:
        with monkeypatch.context() as context:
            context.setattr(os, channel, retry_read if channel == "read" else retry_write)
            return original_capture(stdin, stdout, stderr, source, deadline, output_limit)

    monkeypatch.setattr(supervise, "capture_pipes", capture)
    # Act
    result = run_command(
        responding_command(result_payload(BILINGUAL_SHA256)),
        BILINGUAL_BYTES,
        WorkerLimits(),
    )
    # Assert
    assert result.outcome == "success"
    assert result.text == "synthetic"
    assert retried == [channel]


def test_worker_closing_stdin_cannot_claim_success_without_complete_input() -> None:
    # Arrange
    source = b"x" * (5 * 1024**2)
    source_hash = sha256(source).hexdigest()
    payload = result_payload(source_hash)
    command = worker_command(f"import os\nos.close(0)\nos.write(1, {payload!r})\n")
    # Act
    result = run_command(command, source, WorkerLimits())
    # Assert
    assert result.outcome == "candidate_failure"
    assert result.text is None
    assert result.source_sha256 == source_hash


def test_pipe_close_failure_still_attempts_other_closes_and_leader_reap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    stdout = io.BytesIO()
    stderr = io.BytesIO()
    reaps: list[float] = []

    def failed_close() -> None:
        raise OSError("private synthetic pipe diagnostic")

    def reaped(timeout: float) -> int:
        reaps.append(timeout)
        return 0

    process = SimpleNamespace(
        pid=2**31 - 1,
        stdin=SimpleNamespace(close=failed_close),
        stdout=stdout,
        stderr=stderr,
        wait=reaped,
    )
    monkeypatch.setattr(os, "killpg", lambda pid, sig: None)
    # Act
    with pytest.raises(WorkerCleanupError) as failure:
        supervise._cleanup(cast(subprocess.Popen[bytes], process))
    # Assert
    assert stdout.closed and stderr.closed
    assert reaps == [2]
    assert str(failure.value) == "worker_cleanup_failed"
