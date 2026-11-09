"""Spawn and reap the single reviewed llama.cpp child without a shell."""

import os
import signal
import socket
from collections.abc import Iterator
from contextlib import contextmanager

from .dialogue_error import DialogueError
from .local_model_constants import (
    CONTEXT_TOKENS,
    MODEL_ALIAS,
    SERVER_BINARY,
    SERVER_HOST,
    SERVER_PORT,
    THREADS,
)


def _command(descriptor: int) -> tuple[str, ...]:
    """Use the inherited verified file, CPU-only, and disable optional surfaces."""
    return (
        SERVER_BINARY,
        "--model",
        f"/proc/self/fd/{descriptor}",
        "--host",
        SERVER_HOST,
        "--port",
        str(SERVER_PORT),
        "--alias",
        MODEL_ALIAS,
        "--ctx-size",
        str(CONTEXT_TOKENS),
        "--threads",
        str(THREADS),
        "--threads-batch",
        str(THREADS),
        "--parallel",
        "1",
        "--n-gpu-layers",
        "0",
        "--offline",
        "--no-ui",
        "--no-slots",
        "--no-mmproj",
        "--no-context-shift",
        "--no-warmup",
        "--jinja",
    )


def _require_unused_port() -> None:
    """Refuse occupied loopback before launch; never reuse or stop its listener."""
    with socket.socket() as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind((SERVER_HOST, SERVER_PORT))
        except OSError:
            raise DialogueError("local_model_endpoint_unavailable") from None


def _spawn(descriptor: int) -> int:
    """Preserve the model fd across exec and discard child logs and input.

    POSIX spawn clears close-on-exec for its dup2 action even when both fd
    numbers match. Other Python-acquired descriptors remain close-on-exec.
    """
    command = _command(descriptor)
    actions = [
        (os.POSIX_SPAWN_DUP2, descriptor, descriptor),
        (os.POSIX_SPAWN_OPEN, 0, "/dev/null", os.O_RDONLY, 0),
        (os.POSIX_SPAWN_OPEN, 1, "/dev/null", os.O_WRONLY, 0),
        (os.POSIX_SPAWN_DUP2, 1, 2),
    ]
    try:
        return os.posix_spawn(command[0], command, {"LANG": "C.UTF-8"}, file_actions=actions)
    except OSError:
        raise DialogueError("local_model_runtime_unavailable") from None


def _reap(pid: int) -> None:
    """Kill only the unreaped child, then wait. Its PID cannot be reused before wait."""
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    os.waitpid(pid, 0)


def require_running(pid: int) -> None:
    """Detect an exited child without reaping it; ownership stays with the context."""
    state = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    if state is not None:
        raise DialogueError("local_model_server_exited")


@contextmanager
def owned_server(descriptor: int) -> Iterator[int]:
    """Start only after the port check and always reap this one direct child."""
    _require_unused_port()
    pid = _spawn(descriptor)
    try:
        yield pid
    finally:
        _reap(pid)
