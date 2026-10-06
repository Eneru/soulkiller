"""Transfer bounded bytes without blocking the supervisor on a worker pipe."""

import os
import selectors
from time import monotonic
from typing import IO, Literal

from .worker_constants import PIPE_CHUNK_BYTES


def capture_pipes(
    stdin: IO[bytes],
    stdout: IO[bytes],
    stderr: IO[bytes],
    source: bytes,
    deadline: float,
    output_limit: int,
) -> tuple[Literal["timeout", "output_limit", "candidate_failure"] | None, bytes]:
    """Use one deadline and a combined cap; discard stderr instead of exposing it."""
    response = bytearray()
    output_size = 0
    sent = 0
    incomplete_input = False
    with selectors.DefaultSelector() as selector:
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
        while selector.get_map():
            remaining = deadline - monotonic()
            if remaining <= 0:
                return "timeout", b""
            for key, _ in selector.select(remaining):
                descriptor = key.fd
                if key.data == "stdin":
                    try:
                        written = os.write(
                            descriptor, memoryview(source)[sent : sent + PIPE_CHUNK_BYTES]
                        )
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        written = 0
                    sent += written
                    if written == 0 or sent == len(source):
                        incomplete_input = sent != len(source)
                        selector.unregister(descriptor)
                        stdin.close()
                    continue
                try:
                    chunk = os.read(
                        descriptor, min(PIPE_CHUNK_BYTES, output_limit - output_size + 1)
                    )
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(descriptor)
                    if key.data == "stdout":
                        stdout.close()
                    else:
                        stderr.close()
                    continue
                output_size += len(chunk)
                if output_size > output_limit:
                    return "output_limit", b""
                if key.data == "stdout":
                    response.extend(chunk)
    return ("candidate_failure" if incomplete_input else None), bytes(response)
