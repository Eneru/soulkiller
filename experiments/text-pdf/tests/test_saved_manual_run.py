"""End-to-end save/reopen behavior and scheduling interruption boundaries."""

import json
from importlib import import_module
from pathlib import Path

import pytest

from soulkiller_text.fixture_record import encode_fixture_record
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.load_corpus import load_corpus
from soulkiller_text.run_status import RunStatus
from soulkiller_text.run_store import RunStore, create_run_store
from soulkiller_text.run_store_error import RunStoreError
from soulkiller_text.saved_run import run_saved_corpus
from soulkiller_text.saved_run_reader import read_saved_run
from soulkiller_text.saved_run_writer import manifest_payload
from soulkiller_text.worker_cleanup_error import WorkerCleanupError
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .manual_cli_fixtures import prepare_run


def test_saved_run_reopens_after_source_files_are_removed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stored reference metadata allows reading without a current source file or manifest."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    # Act
    status = run_saved_corpus(tmp_path, "corpus", "example")
    for path in (tmp_path / "corpus").iterdir():
        path.unlink()
    restored, rows = read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert status is restored is RunStatus.COMPLETE
    assert len(rows) == 3
    assert all(row is not None and row.result is not None for row in rows)


def test_repeated_run_preserves_previous_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run name is create-only and cannot replace previous text."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    run_saved_corpus(tmp_path, "corpus", "example")
    before = read_saved_run(tmp_path, "corpus", "example")
    # Act
    with pytest.raises(RunStoreError, match="run_exists"):
        run_saved_corpus(tmp_path, "corpus", "example")
    # Assert
    assert read_saved_run(tmp_path, "corpus", "example") == before


@pytest.mark.parametrize(
    "fault,expected",
    [(KeyboardInterrupt(), RunStatus.CANCELLED), (WorkerCleanupError(), RunStatus.CLEANUP_FAILURE)],
)
def test_interruption_retains_completed_and_unfinished_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: BaseException, expected: RunStatus
) -> None:
    """Caught interruption preserves completed text, unknown active output and unstarted work."""
    # Arrange
    calls = prepare_run(tmp_path, monkeypatch, fault=fault)
    # Act
    status = run_saved_corpus(tmp_path, "corpus", "example")
    restored, rows = read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert status is restored is expected
    assert len(calls) == 2
    assert rows[0] is not None and rows[0].result is not None
    assert rows[1] is not None and rows[1].output_bytes is None
    assert rows[2] is not None and rows[2].output_bytes == 0


def test_checkpoint_failure_prevents_later_worker_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed persistence boundary propagates before the scheduler launches a second child."""
    # Arrange
    calls = prepare_run(tmp_path, monkeypatch)
    original = RunStore.write_record

    def fail_first(self: RunStore, name: str, payload: bytes) -> None:
        """Fail a fixture write while retaining the already committed manifest."""
        if name == "fixture-001":
            raise RunStoreError("storage_unavailable")
        original(self, name, payload)

    monkeypatch.setattr(RunStore, "write_record", fail_first)
    # Act
    with pytest.raises(RunStoreError, match="storage_unavailable"):
        run_saved_corpus(tmp_path, "corpus", "example")
    # Assert
    assert len(calls) == 1
    assert read_saved_run(tmp_path, "corpus", "example") == (None, (None, None, None))


def test_connected_refusal_creates_no_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing external networking enforcement refuses before corpus reads or output creation."""
    # Arrange
    module = import_module("soulkiller_text.saved_run")
    monkeypatch.setattr(module, "has_offline_topology", lambda: False)
    # Act
    with pytest.raises(ValueError, match="offline_environment_required"):
        run_saved_corpus(tmp_path, "missing", "example")
    # Assert
    assert not (tmp_path / ".soulkiller-local").exists()


def test_manifest_only_run_is_explicitly_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stop before any row does not invent zero counts or a completed schedule."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    metadata = manifest_payload(load_corpus(tmp_path, "corpus"))
    with create_run_store(tmp_path, "corpus", "example") as store:
        store.write_record("manifest", metadata)
    # Act
    status, rows = read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert status is None and rows == (None, None, None)


def test_corrupt_saved_row_fails_instead_of_disappearing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stored JSON is validated even when its outer integrity frame is complete."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    metadata = manifest_payload(load_corpus(tmp_path, "corpus"))
    with create_run_store(tmp_path, "corpus", "example") as store:
        store.write_record("manifest", metadata)
        store.write_record("fixture-001", b"{}")
    # Act
    with pytest.raises(ValueError):
        read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert (tmp_path / ".soulkiller-local/evaluation/example/fixture-001").exists()


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"version": 2},
        {"status": "future"},
        {"status": 7},
        {"output_bytes": True},
        {"output_bytes": -1},
        {"output_bytes": None},
        {"output_bytes": 2},
        {"extra": 1},
    ],
)
def test_inspection_rejects_inconsistent_final_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: dict[str, object]
) -> None:
    """A complete integrity frame cannot authenticate a false total or final status."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    fixtures = load_corpus(tmp_path, "corpus")
    summary = {"version": 1, "status": "complete", "output_bytes": 3}
    summary.update(change)
    with create_run_store(tmp_path, "corpus", "example") as store:
        store.write_record("manifest", manifest_payload(fixtures))
        for index, fixture in enumerate(fixtures, start=1):
            result = WorkerResult(WorkerOutcome.SUCCESS, fixture.specification.sha256, "abc")
            row = FixtureRun(fixture.specification, result, 1)
            store.write_record(f"fixture-{index:03}", encode_fixture_record(row))
        store.write_record("summary", json.dumps(summary).encode())
    # Act
    with pytest.raises(ValueError, match="invalid_saved_run"):
        read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert (tmp_path / ".soulkiller-local/evaluation/example/summary").exists()


def test_final_summary_with_missing_rows_is_not_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An existing summary cannot hide absent fixture records."""
    # Arrange
    prepare_run(tmp_path, monkeypatch)
    with create_run_store(tmp_path, "corpus", "example") as store:
        store.write_record("manifest", manifest_payload(load_corpus(tmp_path, "corpus")))
        store.write_record("summary", b'{"version":1,"status":"complete","output_bytes":0}')
    # Act
    with pytest.raises(ValueError, match="invalid_saved_run"):
        read_saved_run(tmp_path, "corpus", "example")
    # Assert
    assert not (tmp_path / ".soulkiller-local/evaluation/example/fixture-001").exists()
