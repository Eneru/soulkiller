"""Cancellation carrying inspectable in-memory records after cleanup."""

from .corpus_run_result import CorpusRunResult


class CorpusRunCancelled(KeyboardInterrupt):
    """Preserve the operator-interruption catch contract and completed records."""

    def __init__(self, result: CorpusRunResult) -> None:
        super().__init__("corpus_run_cancelled")
        self._result = result

    @property
    def result(self) -> CorpusRunResult:
        """Expose the immutable partial run without a writable result attribute."""
        return self._result
