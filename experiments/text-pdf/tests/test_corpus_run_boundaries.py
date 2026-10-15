"""Scheduling boundaries preserve consumed resources and unfinished evidence."""

from importlib import import_module
from pathlib import Path
from types import SimpleNamespace

import pytest

from soulkiller_text.corpus_run_cancelled import CorpusRunCancelled
from soulkiller_text.corpus_run_cleanup_error import CorpusRunCleanupError
from soulkiller_text.run_corpus import run_corpus
from soulkiller_text.run_limits import RunLimits
from soulkiller_text.run_status import RunStatus
from soulkiller_text.worker_cleanup_error import WorkerCleanupError
from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_outcome import WorkerOutcome

from .corpus_run_fixtures import ordered_text_corpus, permit_scheduling, recording_workers


def test_remaining_aggregate_output_clamps_next_worker_allowance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 2)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch, counts=(7, 2))
    limits = RunLimits(output_bytes=10, worker_limits=WorkerLimits(output_bytes=8))
    # Act
    result = run_corpus(tmp_path, "corpus", limits)
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert [call[2].output_bytes for call in calls] == [8, 3]
    assert result.output_bytes == 9


def test_failed_worker_probe_byte_counts_toward_later_aggregate_allowance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 2)
    permit_scheduling(monkeypatch)
    calls = recording_workers(
        monkeypatch, counts=(9, 2), outcomes=(WorkerOutcome.OUTPUT_LIMIT, WorkerOutcome.SUCCESS)
    )
    limits = RunLimits(output_bytes=12, worker_limits=WorkerLimits(output_bytes=8))
    # Act
    result = run_corpus(tmp_path, "corpus", limits)
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert [call[2].output_bytes for call in calls] == [8, 3]
    assert result.output_bytes == 11
    assert result.fixtures[0].output_bytes == 9


@pytest.mark.parametrize("observed", [10, 11])
def test_output_exhaustion_retains_finished_row_and_marks_unstarted_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, observed: int
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch, counts=(observed,))
    # Act
    result = run_corpus(tmp_path, "corpus", RunLimits(output_bytes=10))
    # Assert
    assert result.status is RunStatus.OUTPUT_LIMIT
    assert len(calls) == 1
    assert result.fixtures[0].result is not None
    assert result.fixtures[0].output_bytes == observed
    assert result.output_bytes == observed
    assert all(
        row.result is None
        and row.output_bytes == 0
        and row.unfinished_reason is RunStatus.OUTPUT_LIMIT
        for row in result.fixtures[1:]
    )


def test_exact_output_cap_on_final_finished_row_remains_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 1)
    permit_scheduling(monkeypatch)
    recording_workers(monkeypatch, counts=(10,))
    # Act
    result = run_corpus(tmp_path, "corpus", RunLimits(output_bytes=10))
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert result.output_bytes == 10
    assert result.fixtures[0].unfinished_reason is None


def test_overflow_probe_on_final_row_cannot_be_presented_as_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 1)
    permit_scheduling(monkeypatch)
    recording_workers(monkeypatch, counts=(11,), outcomes=(WorkerOutcome.OUTPUT_LIMIT,))
    # Act
    result = run_corpus(tmp_path, "corpus", RunLimits(output_bytes=10))
    # Assert
    assert result.status is RunStatus.OUTPUT_LIMIT
    assert result.output_bytes == 11
    assert result.fixtures[0].result is not None
    assert result.fixtures[0].result.outcome is WorkerOutcome.OUTPUT_LIMIT


def test_remaining_run_deadline_tightens_next_worker_wall_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, 2)
    clock = [0.0]
    permit_scheduling(monkeypatch, clock)
    calls = recording_workers(monkeypatch, clock=clock, advances=(4.0, 0.25))
    limits = RunLimits(wall_seconds=5, worker_limits=WorkerLimits(wall_seconds=3))
    # Act
    result = run_corpus(tmp_path, "corpus", limits)
    # Assert
    assert result.status is RunStatus.COMPLETE
    assert [call[2].wall_seconds for call in calls] == [3, 1]
    assert [call[2].address_space_bytes for call in calls] == [2 * 1024**3, 2 * 1024**3]


def test_elapsed_corpus_loading_consumes_run_deadline_before_any_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    clock = [0.0]
    permit_scheduling(monkeypatch, clock)
    calls = recording_workers(monkeypatch)
    entry = import_module("soulkiller_text.run_corpus")
    original_load = entry.load_corpus

    def delayed_load(root: Path, path: str) -> object:
        result = original_load(root, path)
        clock[0] = 5.0
        return result

    monkeypatch.setattr(entry, "load_corpus", delayed_load)
    # Act
    result = run_corpus(tmp_path, "corpus", RunLimits(wall_seconds=5))
    # Assert
    assert result.status is RunStatus.TIME_LIMIT
    assert result.output_bytes == 0 and calls == []
    assert all(
        row.result is None and row.unfinished_reason is RunStatus.TIME_LIMIT
        for row in result.fixtures
    )


@pytest.mark.parametrize("count", [1, 3])
def test_deadline_reached_after_return_retains_finished_result_and_stops_schedule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, count: int
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path, count)
    clock = [0.0]
    permit_scheduling(monkeypatch, clock)
    calls = recording_workers(monkeypatch, counts=(7,), clock=clock, advances=(5.0,))
    # Act
    result = run_corpus(tmp_path, "corpus", RunLimits(wall_seconds=5))
    # Assert
    assert result.status is RunStatus.TIME_LIMIT
    assert len(calls) == 1
    assert result.fixtures[0].result is not None and result.fixtures[0].output_bytes == 7
    assert result.output_bytes == 7
    assert all(
        row.result is None and row.unfinished_reason is RunStatus.TIME_LIMIT
        for row in result.fixtures[1:]
    )


@pytest.mark.parametrize("unavailable", ["connected", "waitid", "WNOWAIT", "platform"])
def test_unavailable_environment_prevents_even_txt_only_worker_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, unavailable: str
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch)
    runner = import_module("soulkiller_text.corpus_runner")
    if unavailable == "connected":
        monkeypatch.setattr(runner, "has_offline_topology", lambda: False)
    elif unavailable == "platform":
        monkeypatch.setattr(runner, "sys", SimpleNamespace(platform="win32"))
    else:
        monkeypatch.delattr(runner.os, unavailable)
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.UNSUPPORTED_ENVIRONMENT
    assert result.output_bytes == 0 and calls == []
    assert all(
        row.result is None
        and row.output_bytes == 0
        and row.unfinished_reason is RunStatus.UNSUPPORTED_ENVIRONMENT
        for row in result.fixtures
    )


def test_worker_unavailable_guard_aborts_later_fixtures_and_retains_observation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(
        monkeypatch, counts=(7,), outcomes=(WorkerOutcome.UNSUPPORTED_ENVIRONMENT,)
    )
    # Act
    result = run_corpus(tmp_path, "corpus")
    # Assert
    assert result.status is RunStatus.UNSUPPORTED_ENVIRONMENT
    assert len(calls) == 1
    assert result.fixtures[0].result is not None
    assert result.fixtures[0].result.outcome is WorkerOutcome.UNSUPPORTED_ENVIRONMENT
    assert result.output_bytes == 7
    assert all(
        row.result is None and row.unfinished_reason is RunStatus.UNSUPPORTED_ENVIRONMENT
        for row in result.fixtures[1:]
    )


def test_cancellation_preserves_completed_rows_and_unknown_interrupted_byte_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch, counts=(7,), fault=KeyboardInterrupt())
    # Act
    with pytest.raises(KeyboardInterrupt) as failure:
        run_corpus(tmp_path, "corpus")
    # Assert
    assert isinstance(failure.value, CorpusRunCancelled)
    result = failure.value.result
    assert result.status is RunStatus.CANCELLED and result.output_bytes is None
    assert len(calls) == 2
    assert result.fixtures[0].result is not None and result.fixtures[0].output_bytes == 7
    assert result.fixtures[1].result is None and result.fixtures[1].output_bytes is None
    assert result.fixtures[1].unfinished_reason is RunStatus.CANCELLED
    assert (
        result.fixtures[2].output_bytes == 0
        and result.fixtures[2].unfinished_reason is RunStatus.CANCELLED
    )


def test_cleanup_failure_preserves_base_catch_contract_and_stops_later_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch, counts=(7,), fault=WorkerCleanupError())
    # Act
    with pytest.raises(WorkerCleanupError) as failure:
        run_corpus(tmp_path, "corpus")
    # Assert
    assert isinstance(failure.value, CorpusRunCleanupError)
    result = failure.value.result
    assert result.status is RunStatus.CLEANUP_FAILURE and result.output_bytes is None
    assert len(calls) == 2
    assert result.fixtures[0].result is not None and result.fixtures[0].output_bytes == 7
    assert result.fixtures[1].result is None and result.fixtures[1].output_bytes is None
    assert result.fixtures[1].unfinished_reason is RunStatus.CLEANUP_FAILURE
    assert (
        result.fixtures[2].output_bytes == 0
        and result.fixtures[2].unfinished_reason is RunStatus.CLEANUP_FAILURE
    )


@pytest.mark.parametrize(
    "fault", [KeyboardInterrupt(), WorkerCleanupError()], ids=["cancellation", "cleanup"]
)
def test_exception_partial_result_cannot_be_reassigned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: BaseException
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    recording_workers(monkeypatch, counts=(7,), fault=fault)
    with pytest.raises((CorpusRunCancelled, CorpusRunCleanupError)) as failure:
        run_corpus(tmp_path, "corpus")
    assert isinstance(failure.value, (CorpusRunCancelled, CorpusRunCleanupError))
    original = failure.value.result
    attribute = "result"
    # Act / Assert
    with pytest.raises(AttributeError):
        setattr(failure.value, attribute, original)


def test_cancellation_between_calls_keeps_completed_counts_and_never_started_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    returned = [False]

    def record_return() -> None:
        returned[0] = True

    def interrupted_clock() -> float:
        if returned[0]:
            raise KeyboardInterrupt()
        return 0.0

    calls = recording_workers(monkeypatch, counts=(7,), on_call=record_return)
    monkeypatch.setattr(import_module("soulkiller_text.run_corpus"), "monotonic", interrupted_clock)
    # Act
    with pytest.raises(CorpusRunCancelled) as failure:
        run_corpus(tmp_path, "corpus")
    # Assert
    result = failure.value.result
    assert result.status is RunStatus.CANCELLED and result.output_bytes == 7
    assert len(calls) == 1
    assert result.fixtures[0].result is not None and result.fixtures[0].output_bytes == 7
    assert all(
        row.result is None
        and row.output_bytes == 0
        and row.unfinished_reason is RunStatus.CANCELLED
        for row in result.fixtures[1:]
    )


def test_cancellation_during_environment_validation_marks_all_rows_never_started(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    ordered_text_corpus(tmp_path)
    permit_scheduling(monkeypatch)
    calls = recording_workers(monkeypatch)

    def cancelled_guard() -> bool:
        raise KeyboardInterrupt()

    monkeypatch.setattr(
        import_module("soulkiller_text.corpus_runner"), "has_offline_topology", cancelled_guard
    )
    # Act
    with pytest.raises(CorpusRunCancelled) as failure:
        run_corpus(tmp_path, "corpus")
    # Assert
    result = failure.value.result
    assert result.status is RunStatus.CANCELLED and result.output_bytes == 0
    assert calls == []
    assert all(
        row.result is None
        and row.output_bytes == 0
        and row.unfinished_reason is RunStatus.CANCELLED
        for row in result.fixtures
    )
