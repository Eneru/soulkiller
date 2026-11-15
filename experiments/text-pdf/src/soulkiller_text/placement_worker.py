"""Entry point for a credential-free, one-request placement simulation."""

import sys

from .dialogue_error import DialogueError
from .manual_cli_constants import FAILURE, SUCCESS
from .placement_protocol import FRAME_BYTES, simulated_reply


def main() -> int:
    """Read at most one frame and emit one response without logging either payload."""
    try:
        frame = sys.stdin.buffer.read(FRAME_BYTES + 1)
        sys.stdout.buffer.write(simulated_reply(frame))
        sys.stdout.buffer.flush()
    except (DialogueError, OSError):
        return FAILURE
    return SUCCESS


if __name__ == "__main__":
    raise SystemExit(main())
