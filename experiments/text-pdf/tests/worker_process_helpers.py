"""Real process observations and safe cleanup for synthetic fault probes."""

from __future__ import annotations

import os
import signal
import subprocess
from pathlib import Path
from typing import Any

import pytest


def record_processes(monkeypatch: pytest.MonkeyPatch) -> list[subprocess.Popen[bytes]]:
    """Observe real children without substituting their execution."""
    original = subprocess.Popen
    processes: list[subprocess.Popen[bytes]] = []

    def recording(command: tuple[str, ...], **kwargs: Any) -> subprocess.Popen[bytes]:
        process = original(command, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", recording)
    return processes


def assert_reaped(processes: list[subprocess.Popen[bytes]]) -> None:
    assert len(processes) == 1
    process = processes[0]
    assert process.poll() is not None
    for stream in (process.stdin, process.stdout, process.stderr):
        assert stream is not None and stream.closed


def stop_probe_process(process: subprocess.Popen[bytes]) -> None:
    """Ensure fault-injection tests do not leave a real probe alive."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=2)


def process_is_stopped(pid: int) -> bool:
    """A killed orphan can briefly await init reaping as a zombie."""
    path = Path(f"/proc/{pid}/stat")
    try:
        state = path.read_text(encoding="ascii").split(") ", 1)[1].split()[0]
    except FileNotFoundError:
        return True
    return state == "Z"
