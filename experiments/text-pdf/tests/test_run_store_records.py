"""Immutable complete frames preserve opaque bytes and enforce encoded budgets."""

import os
from pathlib import Path
from typing import cast

import pytest

from soulkiller_text.run_store import create_run_store, open_run_store
from soulkiller_text.run_store_error import RunStoreError

from .run_store_fixtures import (
    HEADER_BYTES,
    RECORD_BYTES,
    RECORD_COUNT,
    RUN_ID,
    complete_frame,
    directory_entries,
    run_directory,
    workspace_with_source,
)


@pytest.mark.parametrize(
    "payload", [b"", b"\x00\xff\x80\r\n", "Texte français — English ✨".encode()]
)
def test_complete_opaque_payload_survives_closing_and_read_only_reopen(
    tmp_path: Path, payload: bytes
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as writer:
        writer.write_record("record", payload)
    # Act
    with open_run_store(workspace, "corpus", RUN_ID) as reader:
        actual = reader.read_record("record")
    # Assert
    assert actual == payload
    assert (run_directory(workspace) / "record").read_bytes() == complete_frame(payload)
    assert directory_entries(run_directory(workspace)) == {"record"}


@pytest.mark.parametrize("name", ["a", "result_0-text", "a" * 64])
def test_safe_record_names_publish_once(tmp_path: Path, name: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record(name, b"Synthetic bytes.")
        actual = store.read_record(name)
    # Assert
    assert actual == b"Synthetic bytes."
    assert directory_entries(run_directory(workspace)) == {name}


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "a.b",
        "a/b",
        "a\\b",
        "A",
        "é",
        "a:b",
        "a\x00",
        "a\ud800",
        "a" * 65,
        ".scratch-partial",
        None,
    ],
)
def test_invalid_record_names_leave_no_output(tmp_path: Path, name: object) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        with pytest.raises(RunStoreError) as failure:
            store.write_record(cast(str, name), b"Synthetic bytes.")
    # Assert
    assert failure.value.category == "invalid_name"
    assert directory_entries(run_directory(workspace)) == set()


@pytest.mark.parametrize("payload", [None, "text", bytearray(b"bytes"), memoryview(b"bytes"), 0])
def test_only_exact_bytes_can_be_written(tmp_path: Path, payload: object) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        with pytest.raises(RunStoreError) as failure:
            store.write_record("record", cast(bytes, payload))
    # Assert
    assert failure.value.category == "invalid_payload"
    assert directory_entries(run_directory(workspace)) == set()


def test_exact_record_encoded_cap_accepts_payload_and_header(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    payload = b"x" * (RECORD_BYTES - HEADER_BYTES)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        store.write_record("maximum", payload)
        actual = store.read_record("maximum")
    # Assert
    assert actual == payload
    assert (run_directory(workspace) / "maximum").stat().st_size == RECORD_BYTES


def test_record_one_encoded_byte_over_cap_creates_no_scratch(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    payload = b"x" * (RECORD_BYTES - HEADER_BYTES + 1)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        with pytest.raises(RunStoreError) as failure:
            store.write_record("oversized", payload)
    # Assert
    assert failure.value.category == "record_too_large"
    assert directory_entries(run_directory(workspace)) == set()


def test_exact_store_encoded_cap_refuses_a_further_empty_record_without_scratch(
    tmp_path: Path,
) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    payload = b"x" * (RECORD_BYTES - HEADER_BYTES)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        for index in range(5):
            store.write_record(f"record-{index}", payload)
        before = directory_entries(run_directory(workspace))
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("extra", b"")
        # Assert
        assert failure.value.category == "store_limit"
        assert directory_entries(run_directory(workspace)) == before
        assert store.read_record("record-0") == payload
    assert (
        sum(path.stat().st_size for path in run_directory(workspace).iterdir()) == 50 * 1024 * 1024
    )


def test_empty_records_consume_count_budget_without_scratch_on_overflow(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        for index in range(RECORD_COUNT):
            store.write_record(f"record-{index}", b"")
        before = directory_entries(run_directory(workspace))
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("extra", b"")
        # Assert
        assert failure.value.category == "record_limit"
        assert directory_entries(run_directory(workspace)) == before
        assert store.read_record("record-0") == b""
    assert len(before) == 34


@pytest.mark.parametrize("kind", ["file", "symlink", "directory", "fifo", "hardlink"])
def test_record_collision_preserves_every_existing_entry(tmp_path: Path, kind: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        run = run_directory(workspace)
        collision = run / "occupied"
        target = workspace / "corpus" / "source.txt"
        if kind == "file":
            collision.write_bytes(b"Keep original.")
        elif kind == "directory":
            collision.mkdir()
        elif kind == "fifo":
            os.mkfifo(collision)
        elif kind == "hardlink":
            os.link(target, collision)
        else:
            collision.symlink_to(target)
        before = collision.lstat()
        # Act
        with pytest.raises(RunStoreError) as failure:
            store.write_record("occupied", b"Replacement forbidden.")
        # Assert
        assert failure.value.category == "record_exists"
        assert collision.lstat() == before
        assert target.read_bytes() == b"Synthetic source."


def test_read_only_handle_refuses_writes_without_state_change(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as writer:
        writer.write_record("original", b"Keep bytes.")
    before = directory_entries(run_directory(workspace))
    # Act
    with open_run_store(workspace, "corpus", RUN_ID) as reader:
        with pytest.raises(RunStoreError) as failure:
            reader.write_record("extra", b"Forbidden.")
    # Assert
    assert failure.value.category == "read_only"
    assert directory_entries(run_directory(workspace)) == before


@pytest.mark.parametrize("operation", ["read", "write"])
def test_closed_handle_cannot_access_records(tmp_path: Path, operation: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    store = create_run_store(workspace, "corpus", RUN_ID)
    store.write_record("original", b"Keep bytes.")
    store.close()
    store.close()
    # Act
    with pytest.raises(RunStoreError) as failure:
        if operation == "read":
            store.read_record("original")
        else:
            store.write_record("extra", b"Forbidden.")
    # Assert
    assert failure.value.category == "closed"
    assert directory_entries(run_directory(workspace)) == {"original"}


@pytest.mark.parametrize(
    "mutation",
    ["magic", "length", "digest", "truncated-header", "truncated-body", "trailing", "huge-length"],
)
def test_incomplete_or_corrupt_frames_are_not_exposed(tmp_path: Path, mutation: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    frame = complete_frame(b"Original synthetic bytes.")
    damaged = {
        "magic": b"INVALID\n" + frame[8:],
        "length": frame[:8] + (1).to_bytes(8, "big") + frame[16:],
        "digest": frame[:16] + b"x" * 32 + frame[48:],
        "truncated-header": frame[:47],
        "truncated-body": frame[:-1],
        "trailing": frame + b"x",
        "huge-length": frame[:8] + (2**64 - 1).to_bytes(8, "big") + frame[16:],
    }[mutation]
    with create_run_store(workspace, "corpus", RUN_ID):
        (run_directory(workspace) / "damaged").write_bytes(damaged)
    # Act
    with open_run_store(workspace, "corpus", RUN_ID) as store:
        with pytest.raises(RunStoreError) as failure:
            store.read_record("damaged")
    # Assert
    assert failure.value.category == "invalid_record"
    assert (run_directory(workspace) / "damaged").read_bytes() == damaged


@pytest.mark.parametrize("kind", ["symlink", "directory", "fifo", "hardlink", "oversized"])
def test_unsafe_record_entries_are_never_accepted(tmp_path: Path, kind: str) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        run = run_directory(workspace)
        record = run / "unsafe"
        target = workspace / "corpus" / "source.txt"
        if kind == "directory":
            record.mkdir()
        elif kind == "fifo":
            os.mkfifo(record)
        elif kind == "symlink":
            record.symlink_to(target)
        elif kind == "hardlink":
            os.link(target, record)
        else:
            with record.open("wb") as stream:
                stream.truncate(RECORD_BYTES + 1)
        before = record.lstat()
        # Act
        with pytest.raises(RunStoreError):
            store.read_record("unsafe")
        # Assert
        assert record.lstat() == before
        assert target.read_bytes() == b"Synthetic source."


def test_missing_record_returns_safe_category(tmp_path: Path) -> None:
    # Arrange
    workspace = workspace_with_source(tmp_path)
    # Act
    with create_run_store(workspace, "corpus", RUN_ID) as store:
        with pytest.raises(RunStoreError) as failure:
            store.read_record("missing")
    # Assert
    assert failure.value.category == "record_unavailable"
    assert failure.value.args == ("record_unavailable",)
