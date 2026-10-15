"""Fault injection preserves completed records and closes acquired descriptors."""

import errno
import os
from pathlib import Path

import pytest

from soulkiller_text import confined_files
from soulkiller_text.run_store import create_run_store, open_run_store
from soulkiller_text.run_store_error import RunStoreError

from .run_store_fixtures import (
    RUN_ID,
    assert_descriptors_closed,
    directory_entries,
    run_directory,
    track_descriptors,
    workspace_with_source,
)


def test_short_writes_are_accumulated_until_the_complete_frame_is_published(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_write = os.write
    writes: list[int] = []

    def short_write(descriptor: int, payload: bytes | memoryview) -> int:
        written = original_write(descriptor, payload[:3])
        writes.append(written)
        return written

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        monkeypatch.setattr(os, "write", short_write)
        # Act
        store.write_record("complete", b"Complete synthetic bytes.")
        actual = store.read_record("complete")
    # Assert
    assert actual == b"Complete synthetic bytes."
    assert len(writes) > 1
    assert all(0 < count <= 3 for count in writes)
    assert directory_entries(run_directory(workspace)) == {"complete"}


@pytest.mark.parametrize("fault", ["zero", "disk-full", "cancellation"])
def test_failed_later_write_preserves_prior_record_and_poisoned_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)

    def failed_write(descriptor: int, payload: bytes | memoryview) -> int:
        if fault == "zero":
            return 0
        if fault == "cancellation":
            raise KeyboardInterrupt
        raise OSError(errno.ENOSPC, "Synthetic failure with private diagnostics.")

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("earlier", b"Completed earlier.")
        monkeypatch.setattr(os, "write", failed_write)
        expected = KeyboardInterrupt if fault == "cancellation" else RunStoreError
        # Act
        with pytest.raises(expected):
            store.write_record("unfinished", b"Must not become accepted.")
        with pytest.raises(RunStoreError) as poisoned:
            store.write_record("retry", b"Forbidden.")
        actual = store.read_record("earlier")
    # Assert
    assert actual == b"Completed earlier."
    assert poisoned.value.category == "write_failed"
    names = directory_entries(run_directory(workspace))
    assert "unfinished" not in names
    assert "retry" not in names
    assert len(names - {"earlier"}) == 1


@pytest.mark.parametrize("phase", ["file-sync", "link", "unlink", "directory-sync"])
def test_publication_failures_are_not_success_and_keep_earlier_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, phase: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_fsync = os.fsync
    sync_calls = 0

    def failed_sync(descriptor: int) -> None:
        nonlocal sync_calls
        sync_calls += 1
        if sync_calls == (1 if phase == "file-sync" else 2):
            raise OSError(errno.EIO, "Synthetic sync failure.")
        original_fsync(descriptor)

    def failed_link(*args: object, **kwargs: object) -> None:
        raise OSError(errno.EIO, "Synthetic publication failure.")

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("earlier", b"Completed earlier.")
        if phase in {"file-sync", "directory-sync"}:
            monkeypatch.setattr(os, "fsync", failed_sync)
        else:
            monkeypatch.setattr(os, phase, failed_link)
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("unfinished", b"Later synthetic bytes.")
        with pytest.raises(RunStoreError) as poisoned:
            store.write_record("retry", b"Forbidden.")
        actual = store.read_record("earlier")
    # Assert
    assert failure.value.args == ("storage_unavailable",)
    assert poisoned.value.category == "write_failed"
    assert actual == b"Completed earlier."
    assert "retry" not in directory_entries(run_directory(workspace))


def test_unlinked_scratch_failure_does_not_accept_multiply_linked_final_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)

    def failed_unlink(*args: object, **kwargs: object) -> None:
        raise OSError(errno.EIO, "Synthetic unlink failure.")

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        monkeypatch.setattr(os, "unlink", failed_unlink)
        # Act
        with pytest.raises(RunStoreError):
            store.write_record("uncertain", b"Uncertain publication.")
        with pytest.raises(RunStoreError) as failure:
            store.read_record("uncertain")
    # Assert
    assert failure.value.category == "invalid_record"
    assert (run_directory(workspace) / "uncertain").stat().st_nlink == 2


def test_partial_scratch_cannot_be_read_through_the_public_record_api(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)

    def stopped_write(descriptor: int, payload: bytes | memoryview) -> int:
        raise KeyboardInterrupt

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        monkeypatch.setattr(os, "write", stopped_write)
        with pytest.raises(KeyboardInterrupt):
            store.write_record("unfinished", b"Incomplete.")
        scratch = next(iter(directory_entries(run_directory(workspace))))
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.read_record(scratch)
    # Assert
    assert failure.value.category == "invalid_name"
    assert "unfinished" not in directory_entries(run_directory(workspace))


@pytest.mark.parametrize("mutation", ["append", "same-size", "hardlink"])
def test_record_revision_changes_during_read_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_read = os.read
    mutated = False
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("record", b"Original bytes.")
        path = run_directory(workspace) / "record"

        def mutating_read(descriptor: int, count: int) -> bytes:
            nonlocal mutated
            if not mutated:
                mutated = True
                if mutation == "append":
                    with path.open("ab") as stream:
                        stream.write(b"extra")
                elif mutation == "same-size":
                    path.write_bytes(b"x" * path.stat().st_size)
                else:
                    os.link(path, path.with_name("extra-link"))
            return original_read(descriptor, count)

        monkeypatch.setattr(os, "read", mutating_read)
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.read_record("record")
    # Assert
    assert failure.value.category == "invalid_record"
    assert mutated


def test_record_replaced_by_symlink_before_acquisition_is_not_followed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_open = confined_files._open_leaf
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("record", b"Original.")
        record = run_directory(workspace) / "record"
        target = workspace / "corpus" / "source.txt"

        def replaced_open(parent: int, name: str) -> int:
            record.rename(record.with_name("original"))
            record.symlink_to(target)
            return original_open(parent, name)

        monkeypatch.setattr(confined_files, "_open_leaf", replaced_open)
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.read_record("record")
    # Assert
    assert failure.value.category == "invalid_record"
    assert target.read_bytes() == b"Synthetic source."


@pytest.mark.parametrize("failure", [False, True])
def test_record_file_descriptors_close_after_success_or_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: bool
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired: list[int] = []
    original_open = confined_files._open_leaf

    def tracked_open(parent: int, name: str) -> int:
        descriptor = original_open(parent, name)
        acquired.append(descriptor)
        return descriptor

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("record", b"Original.")
        if failure:
            (run_directory(workspace) / "record").write_bytes(b"Truncated.")
        monkeypatch.setattr(confined_files, "_open_leaf", tracked_open)
        # Act
        if failure:
            with pytest.raises(RunStoreError):
                store.read_record("record")
        else:
            assert store.read_record("record") == b"Original."
        # Assert
        assert len(acquired) == 1
        with pytest.raises(OSError) as closed:
            os.fstat(acquired[0])
        assert closed.value.errno == errno.EBADF


def test_context_exception_closes_store_and_preserves_completed_record(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with pytest.raises(KeyboardInterrupt), create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("earlier", b"Completed earlier.")
        raise KeyboardInterrupt
    # Assert
    with pytest.raises(RunStoreError) as failure:
        store.read_record("earlier")
    assert failure.value.category == "closed"
    with open_run_store(workspace, "corpus", RUN_ID) as reader:
        assert reader.read_record("earlier") == b"Completed earlier."


def test_transient_interrupted_write_retries_without_losing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_write = os.write
    interrupted = False

    def interrupted_write(descriptor: int, payload: bytes | memoryview) -> int:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise InterruptedError(errno.EINTR, "Synthetic interruption.")
        return original_write(descriptor, payload)

    with create_run_store(workspace, "corpus", RUN_ID) as store:
        monkeypatch.setattr(os, "write", interrupted_write)
        # Act
        store.write_record("record", b"Complete after interruption.")
        actual = store.read_record("record")
    # Assert
    assert interrupted
    assert actual == b"Complete after interruption."
    assert directory_entries(run_directory(workspace)) == {"record"}


def test_normal_context_closes_every_acquired_directory_and_scratch_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired = track_descriptors(monkeypatch)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("record", b"Complete synthetic record.")
        actual = store.read_record("record")
    # Assert
    assert actual == b"Complete synthetic record."
    assert acquired
    assert_descriptors_closed(acquired)


def test_initial_directory_identity_failure_closes_the_duplicated_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired = track_descriptors(monkeypatch)

    def failed_fstat(descriptor: int) -> os.stat_result:
        raise OSError(errno.EIO, "Synthetic initial identity failure.")

    with monkeypatch.context() as fault:
        fault.setattr(os, "fstat", failed_fstat)
        # Act
        with pytest.raises(RunStoreError) as failure:
            create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "storage_unavailable"
    assert acquired
    assert_descriptors_closed(acquired)
    assert directory_entries(workspace) == {"corpus"}


def test_directory_sync_failure_preserves_created_state_and_closes_descriptors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired = track_descriptors(monkeypatch)

    def failed_fsync(descriptor: int) -> None:
        raise OSError(errno.EIO, "Synthetic directory synchronization failure.")

    monkeypatch.setattr(os, "fsync", failed_fsync)
    # Act
    with pytest.raises(RunStoreError) as failure:
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert failure.value.category == "storage_unavailable"
    assert directory_entries(workspace) == {"corpus", ".soulkiller-local"}
    assert_descriptors_closed(acquired)


def test_cancellation_after_run_acquisition_closes_every_owned_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired = track_descriptors(monkeypatch)
    original_close = os.close
    original_open = os.open
    run_acquired = False
    interrupted = False

    def observed_open(
        path: str, flags: int, mode: int = 0o777, *, dir_fd: int | None = None
    ) -> int:
        nonlocal run_acquired
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        if path == RUN_ID:
            run_acquired = True
        return descriptor

    def cancelled_close(descriptor: int) -> None:
        nonlocal interrupted
        original_close(descriptor)
        if run_acquired and not interrupted:
            interrupted = True
            raise KeyboardInterrupt

    monkeypatch.setattr(os, "open", observed_open)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {observed_open})
    monkeypatch.setattr(os, "close", cancelled_close)
    # Act
    with pytest.raises(KeyboardInterrupt):
        create_run_store(workspace, "corpus", RUN_ID)
    # Assert
    assert interrupted
    assert run_directory(workspace).is_dir()
    assert_descriptors_closed(acquired)


@pytest.mark.parametrize("mutation", ["symlink", "hardlink", "truncated"])
def test_changed_scratch_inode_cannot_be_published_as_a_complete_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    original_fsync = os.fsync
    changed = False
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("earlier", b"Completed earlier.")
        run = run_directory(workspace)

        def changed_scratch(descriptor: int) -> None:
            nonlocal changed
            original_fsync(descriptor)
            if not changed:
                changed = True
                scratch = next(path for path in run.iterdir() if path.name.startswith("."))
                if mutation == "symlink":
                    scratch.rename(run / "saved-scratch")
                    scratch.symlink_to(workspace / "corpus" / "source.txt")
                elif mutation == "hardlink":
                    os.link(scratch, run / "extra-link")
                else:
                    scratch.write_bytes(b"Truncated.")

        monkeypatch.setattr(os, "fsync", changed_scratch)
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("unfinished", b"Later synthetic bytes.")
        actual = store.read_record("earlier")
    # Assert
    assert failure.value.category == "unsafe_path"
    assert actual == b"Completed earlier."
    assert "unfinished" not in directory_entries(run)
    assert (workspace / "corpus" / "source.txt").read_bytes() == b"Synthetic source."


def test_failed_write_closes_scratch_and_directory_descriptors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    acquired = track_descriptors(monkeypatch)

    def failed_write(descriptor: int, payload: bytes | memoryview) -> int:
        raise OSError(errno.ENOSPC, "Synthetic full volume.")

    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        monkeypatch.setattr(os, "write", failed_write)
        with pytest.raises(RunStoreError) as failure:
            store.write_record("unfinished", b"Cannot complete.")
    # Assert
    assert failure.value.category == "storage_unavailable"
    assert_descriptors_closed(acquired)
    assert len(directory_entries(run_directory(workspace))) == 1
