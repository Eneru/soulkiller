"""An immutable supervised decoding result."""

from dataclasses import dataclass

from .worker_outcome import WorkerOutcome


@dataclass(frozen=True)
class WorkerResult:
    """Failed outcomes retain a source hash but never partial text or stderr."""

    outcome: WorkerOutcome
    source_sha256: str
    text: str | None
