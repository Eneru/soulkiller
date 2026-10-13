"""Immutable in-memory outcomes for one accepted synthetic corpus."""

from dataclasses import dataclass

from .fixture_run import FixtureRun
from .run_status import RunStatus


@dataclass(frozen=True)
class CorpusRunResult:
    """Unknown interrupted transport counts remain unavailable rather than zero."""

    status: RunStatus
    fixtures: tuple[FixtureRun, ...]
    output_bytes: int | None
