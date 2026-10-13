"""Public accepted-corpus entry for one bounded in-memory extraction pass."""

from pathlib import Path
from time import monotonic

from .corpus_run_result import CorpusRunResult
from .corpus_runner import CorpusRunner
from .load_corpus import load_corpus
from .run_limits import RunLimits


def _validated_limits(limits: RunLimits | None) -> RunLimits:
    if limits is None:
        return RunLimits()
    if type(limits) is not RunLimits:
        raise ValueError("invalid_run_limits")
    return RunLimits(limits.wall_seconds, limits.output_bytes, limits.worker_limits)


def run_corpus(
    workspace_root: Path, corpus_path: str, limits: RunLimits | None = None
) -> CorpusRunResult:
    """Validate all snapshots before work; caller-owned in-memory results are not reports."""
    profile = _validated_limits(limits)
    started_at = monotonic()
    fixtures = load_corpus(workspace_root, corpus_path)
    return CorpusRunner(fixtures, profile, started_at, monotonic).run()
