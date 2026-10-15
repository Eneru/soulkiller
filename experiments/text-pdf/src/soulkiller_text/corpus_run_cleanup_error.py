"""Unconfirmed worker cleanup carrying immutable partial corpus records."""

from .corpus_run_result import CorpusRunResult
from .worker_cleanup_error import WorkerCleanupError


class CorpusRunCleanupError(WorkerCleanupError):
    """Keep the existing cleanup-error catch contract and prohibit continuation."""

    def __init__(self, result: CorpusRunResult) -> None:
        super().__init__()
        self._result = result

    @property
    def result(self) -> CorpusRunResult:
        """Expose the immutable partial run without a writable result attribute."""
        return self._result
