"""Transfer bounded bytes without blocking the supervisor on a worker pipe."""

import os
import selectors
from collections.abc import Callable
from time import monotonic
from typing import IO

from .worker_constants import PIPE_CHUNK_BYTES
from .worker_outcome import WorkerOutcome


def _register_streams(
    selector: selectors.BaseSelector,
    stdin: IO[bytes],
    stdout: IO[bytes],
    stderr: IO[bytes],
    source: bytes,
) -> None:
    """Enable nonblocking transfer, closing empty input before registration."""
    for stream, channel, event in (
        (stdin, "stdin", selectors.EVENT_WRITE),
        (stdout, "stdout", selectors.EVENT_READ),
        (stderr, "stderr", selectors.EVENT_READ),
    ):
        os.set_blocking(stream.fileno(), False)
        if channel == "stdin" and not source:
            stream.close()
        else:
            selector.register(stream, event, channel)


def _write_input(
    selector: selectors.BaseSelector, stdin: IO[bytes], source: bytes, sent: int
) -> tuple[int, bool]:
    """Send one chunk and distinguish complete delivery from early closure."""
    try:
        written = os.write(stdin.fileno(), memoryview(source)[sent : sent + PIPE_CHUNK_BYTES])
    except BlockingIOError:
        return sent, False
    except BrokenPipeError:
        written = 0
    sent += written
    if written == 0 or sent == len(source):
        selector.unregister(stdin)
        stdin.close()
        return sent, sent != len(source)
    return sent, False


def _read_output(
    selector: selectors.BaseSelector, stream: IO[bytes], remaining_budget: int
) -> bytes | None:
    """Read at most one overflow byte; unregister and close the stream on EOF."""
    try:
        chunk = os.read(stream.fileno(), min(PIPE_CHUNK_BYTES, remaining_budget + 1))
    except BlockingIOError:
        return None
    if not chunk:
        selector.unregister(stream)
        stream.close()
    return chunk


def capture_pipes(
    stdin: IO[bytes],
    stdout: IO[bytes],
    stderr: IO[bytes],
    source: bytes,
    deadline: float,
    output_limit: int,
    *,
    output_observer: Callable[[int], None] | None = None,
) -> tuple[WorkerOutcome | None, bytes]:
    """Use one deadline and a combined cap; discard stderr instead of exposing it."""
    response = bytearray()
    output_size = 0
    sent = 0
    incomplete_input = False
    with selectors.DefaultSelector() as selector:
        _register_streams(selector, stdin, stdout, stderr, source)
        while selector.get_map():
            remaining = deadline - monotonic()
            if remaining <= 0:
                return WorkerOutcome.TIMEOUT, b""
            for key, _ in selector.select(remaining):
                if key.data == "stdin":
                    sent, incomplete_input = _write_input(selector, stdin, source, sent)
                    continue
                stream = stdout if key.data == "stdout" else stderr
                chunk = _read_output(selector, stream, output_limit - output_size)
                if not chunk:
                    continue
                if output_observer is not None:
                    output_observer(len(chunk))
                output_size += len(chunk)
                if output_size > output_limit:
                    return WorkerOutcome.OUTPUT_LIMIT, b""
                if key.data == "stdout":
                    response.extend(chunk)
    failure = WorkerOutcome.CANDIDATE_FAILURE if incomplete_input else None
    return failure, bytes(response)
