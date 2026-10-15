"""Schedule fixed trusted workers under aggregate time and transport guards."""

import os
import sys
from collections.abc import Callable

from .corpus_run_cancelled import CorpusRunCancelled
from .corpus_run_cleanup_error import CorpusRunCleanupError
from .corpus_run_result import CorpusRunResult
from .fixture_run import FixtureRun
from .loaded_fixture import LoadedFixture
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_worker import run_observed_pdf_worker
from .pdf_worker_result import PdfWorkerResult
from .run_limits import RunLimits
from .run_status import RunStatus
from .run_text_worker import run_observed_text_worker
from .worker_cleanup_error import WorkerCleanupError
from .worker_execution import WorkerExecution
from .worker_limits import WorkerLimits
from .worker_network_guard import has_offline_topology
from .worker_outcome import WorkerOutcome
from .worker_result import WorkerResult


class CorpusRunner:
    """Own ordered accepted snapshots and immutable observations, never file paths."""

    def __init__(
        self,
        fixtures: tuple[LoadedFixture, ...],
        limits: RunLimits,
        started_at: float,
        clock: Callable[[], float],
    ) -> None:
        self._fixtures = fixtures
        self._limits = limits
        self._deadline = started_at + limits.wall_seconds
        self._clock = clock
        self._records: list[FixtureRun] = []
        self._output_bytes = 0
        self._active_index: int | None = None

    def run(self) -> CorpusRunResult:
        """Stop on absent guards or interruption without scheduling later workers."""
        try:
            if not self._environment_supported():
                return self._finish(RunStatus.UNSUPPORTED_ENVIRONMENT)
            return self._schedule()
        except WorkerCleanupError:
            raise CorpusRunCleanupError(self._finish(RunStatus.CLEANUP_FAILURE)) from None
        except KeyboardInterrupt:
            raise CorpusRunCancelled(self._finish(RunStatus.CANCELLED)) from None

    def _environment_supported(self) -> bool:
        return (
            sys.platform == "linux"
            and hasattr(os, "waitid")
            and hasattr(os, "WNOWAIT")
            and has_offline_topology()
        )

    def _schedule(self) -> CorpusRunResult:
        for fixture in self._fixtures:
            worker_limits = self._next_allowance()
            if isinstance(worker_limits, RunStatus):
                return self._finish(worker_limits)
            self._active_index = len(self._records)
            execution = self._execute(fixture, worker_limits)
            self._records.append(
                FixtureRun(fixture.specification, execution.result, execution.output_bytes)
            )
            self._output_bytes += execution.output_bytes
            self._active_index = None
            status = self._returned_status(execution.result)
            if status is not None:
                return self._finish(status)
        return self._finish(RunStatus.COMPLETE)

    def _next_allowance(self) -> WorkerLimits | RunStatus:
        remaining_wall = self._deadline - self._clock()
        if remaining_wall <= 0:
            return RunStatus.TIME_LIMIT
        remaining_output = self._limits.output_bytes - self._output_bytes
        if remaining_output <= 0:
            return RunStatus.OUTPUT_LIMIT
        worker = self._limits.worker_limits
        return WorkerLimits(
            wall_seconds=min(worker.wall_seconds, remaining_wall),
            address_space_bytes=worker.address_space_bytes,
            output_bytes=min(worker.output_bytes, remaining_output),
        )

    def _execute(
        self, fixture: LoadedFixture, limits: WorkerLimits
    ) -> WorkerExecution[WorkerResult] | WorkerExecution[PdfWorkerResult]:
        if isinstance(fixture.specification, PdfCorpusFixture):
            return run_observed_pdf_worker(
                fixture.source, limits, max_pages=fixture.specification.page_count
            )
        return run_observed_text_worker(fixture.source, limits)

    def _returned_status(self, result: WorkerResult | PdfWorkerResult) -> RunStatus | None:
        if self._output_bytes > self._limits.output_bytes:
            return RunStatus.OUTPUT_LIMIT
        if result.outcome == WorkerOutcome.UNSUPPORTED_ENVIRONMENT:
            return RunStatus.UNSUPPORTED_ENVIRONMENT
        if self._clock() >= self._deadline:
            return RunStatus.TIME_LIMIT
        if self._output_bytes == self._limits.output_bytes and len(self._records) < len(
            self._fixtures
        ):
            return RunStatus.OUTPUT_LIMIT
        return None

    def _finish(self, status: RunStatus) -> CorpusRunResult:
        completed_count = len(self._records)
        unfinished = tuple(
            FixtureRun(
                fixture.specification,
                output_bytes=None if index == self._active_index else 0,
                unfinished_reason=status,
            )
            for index, fixture in enumerate(self._fixtures[completed_count:], start=completed_count)
        )
        records = tuple(self._records) + unfinished
        observed_bytes = (
            None
            if any(record.output_bytes is None for record in records)
            else sum(record.output_bytes for record in records if record.output_bytes is not None)
        )
        return CorpusRunResult(status, records, observed_bytes)
