"""One-shot stdio worker for the pinned offline Qwen3-4B comparison."""

import os
import sys
from pathlib import Path

from .dialogue_error import DialogueError
from .local_model import complete_under_deadline
from .local_model_budget import local_deadline, require_local_budget
from .local_model_profiles import QWEN_4B
from .manual_cli_constants import FAILURE, SUCCESS
from .placement_protocol import FRAME_BYTES, VERSION, reviewed_request
from .saved_json import decode_saved, encode_saved

SESSION_SECONDS = 170
CGROUP_ROOT = Path("/sys/fs/cgroup")
INVALID_ENVIRONMENT = "invalid_placement_worker_environment"


def _memory_peak() -> int:
    """Read the kernel's cgroup peak including file cache, with no host identifiers."""
    peak = int((CGROUP_ROOT / "memory.peak").read_text())
    if peak <= 0:
        raise DialogueError(INVALID_ENVIRONMENT)
    return peak


def _run(workspace: Path) -> bytes:
    """Read one reviewed frame and record measurements from the pinned CPU runtime."""
    require_local_budget()
    if (CGROUP_ROOT / "memory.swap.max").read_text().strip() != "0":
        raise DialogueError(INVALID_ENVIRONMENT)
    messages, ids = reviewed_request(sys.stdin.buffer.read(FRAME_BYTES + 1))
    observations: dict[str, int] = {}

    def observe(phase: str, elapsed_ms: int, prompt_tokens: int, completion_tokens: int) -> None:
        """Record numeric runtime measurements without capturing model output or logs."""
        observations[f"{phase}_ms"] = elapsed_ms
        if phase == "generation":
            observations["prompt_tokens"] = prompt_tokens
            observations["completion_tokens"] = completion_tokens

    completion = complete_under_deadline(
        messages, ids, workspace=workspace, profile=QWEN_4B, observe=observe
    )
    observations["memory_peak_bytes"] = _memory_peak()
    frame = encode_saved(
        {
            "version": VERSION,
            "completion": decode_saved(completion.payload),
            "metrics": observations,
        }
    )
    if len(frame) > FRAME_BYTES:
        raise DialogueError("placement_worker_output_limit")
    return frame


def _write(frame: bytes) -> None:
    """Write on the owning stdout descriptor without a buffered retry after disconnect."""
    remaining = memoryview(frame)
    while remaining:
        written = os.write(sys.stdout.fileno(), remaining)
        if written <= 0:
            raise OSError("placement_worker_output_closed")
        remaining = remaining[written:]


def main() -> int:
    """Bound stdin, model ownership and stdout under one Linux SIGALRM deadline."""
    try:
        with local_deadline(SESSION_SECONDS):
            _write(_run(Path.cwd()))
    except (DialogueError, OSError, ValueError):
        return FAILURE
    return SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
