"""Use the bounded Linux subprocess supervisor to exercise the placement wire format."""

import sys
from pathlib import Path

from .dialogue import Messages
from .dialogue_constants import DIALOGUE_CORPUS
from .dialogue_error import DialogueError
from .model_completion import ModelCompletion
from .placement_cases import CASES, NO_MATCH_CASE
from .placement_protocol import FRAME_BYTES, read_reply, request_frame
from .supervise import run_command
from .worker_cleanup_error import WorkerCleanupError
from .worker_limits import WorkerLimits
from .worker_outcome import WorkerOutcome

SIMULATION_LIMITS = WorkerLimits(wall_seconds=5, output_bytes=FRAME_BYTES)
# -I excludes ambient Python paths. The supervisor fixes the environment and
# this bootstrap adds only the colocated source directory from the client.
BOOTSTRAP = (
    "import sys; sys.path.insert(0, sys.argv[1]); "
    "from soulkiller_text.placement_worker import main; raise SystemExit(main())"
)


def approved_prompt(corpus: str, language: str, query: str, question: str) -> str | None:
    """Admit only exact trial arguments before reading saved evidence."""
    case = (language, query, question)
    if corpus != DIALOGUE_CORPUS or (case not in CASES and case != NO_MATCH_CASE):
        raise DialogueError("unapproved_placement_case")
    return CASES[case][0] if case in CASES else None


def _classify(
    exit_code: int | None, failure: WorkerOutcome | None, response: bytes, _digest: str
) -> ModelCompletion:
    """Return only a clean bounded response, without leaking the worker's diagnostics."""
    if failure is WorkerOutcome.TIMEOUT or (failure is None and exit_code is None):
        raise DialogueError("placement_worker_timeout")
    if exit_code != 0 or failure is not None:
        raise DialogueError("placement_worker_failed")
    return read_reply(response)


def simulate_completion(
    messages: Messages, ids: tuple[str, ...], *, expected: str | None
) -> ModelCompletion:
    """Send approved bytes to one fixed child and rely on the supervisor to reap its group."""
    frame = request_frame(messages, ids, expected)
    source = str(Path(__file__).resolve().parents[1])
    command = (sys.executable, "-I", "-B", "-c", BOOTSTRAP, source)
    try:
        return run_command(command, frame, SIMULATION_LIMITS, _classify)
    except WorkerCleanupError:
        raise DialogueError("placement_worker_cleanup_failed") from None
