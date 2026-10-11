"""Trusted synthetic commands and independently authored worker responses."""

import json
import sys
from pathlib import Path


def worker_command(script: str) -> tuple[str, ...]:
    """Run a fixed test script without a shell or inherited Python startup hooks."""
    return (sys.executable, "-I", "-B", "-c", script)


def result_payload(
    source_sha256: str, outcome: str = "success", text: str | None = "synthetic"
) -> bytes:
    """Author expected wire records independently from the production encoder."""
    return json.dumps(
        {"version": 1, "outcome": outcome, "source_sha256": source_sha256, "text": text},
        ensure_ascii=True,
    ).encode("ascii")


def responding_command(payload: bytes, exit_code: int = 0, stderr: bytes = b"") -> tuple[str, ...]:
    return worker_command(
        "import sys\n"
        "sys.stdin.buffer.read()\n"
        f"sys.stdout.buffer.write({payload!r})\n"
        "sys.stdout.buffer.flush()\n"
        f"sys.stderr.buffer.write({stderr!r})\n"
        "sys.stderr.buffer.flush()\n"
        f"sys.exit({exit_code})\n"
    )


def blocking_command() -> tuple[str, ...]:
    return worker_command("import time\ntime.sleep(60)\n")


def flooding_command(descriptor: int) -> tuple[str, ...]:
    return worker_command(f"import os\nwhile True:\n    os.write({descriptor}, b'x' * 4096)\n")


def memory_failure_command(source_sha256: str) -> tuple[str, ...]:
    payload = result_payload(source_sha256, "resource_limit", None)
    return worker_command(
        "import resource, sys\n"
        "sys.stdin.buffer.read()\n"
        "resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**2, 64 * 1024**2))\n"
        "try:\n"
        "    bytearray(128 * 1024**2)\n"
        "except MemoryError:\n"
        f"    sys.stdout.buffer.write({payload!r})\n"
        "    sys.stdout.buffer.flush()\n"
    )


def inherited_pipe_command(child_pid_path: Path) -> tuple[str, ...]:
    """Leave a trusted descendant in the same process group with inherited pipes."""
    return worker_command(
        "import os, time\n"
        "child = os.fork()\n"
        "if child == 0:\n"
        "    time.sleep(60)\n"
        "    os._exit(0)\n"
        f"with open({str(child_pid_path)!r}, 'w', encoding='ascii') as stream:\n"
        "    stream.write(str(child))\n"
        "os._exit(0)\n"
    )
