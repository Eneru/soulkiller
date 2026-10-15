"""Independent synthetic workspaces and binary frames for run-store behavior tests."""

import errno
import hashlib
import os
import struct
from pathlib import Path

import pytest

RUN_ID = "synthetic-run"
HEADER_BYTES = 48
RECORD_BYTES = 10 * 1024 * 1024
STORE_BYTES = 50 * 1024 * 1024
RECORD_COUNT = 34


def workspace_with_source(root: Path) -> Path:
    """Create a fresh trusted workspace containing a separate synthetic source."""
    workspace = root / "workspace"
    (workspace / "corpus").mkdir(parents=True)
    (workspace / "corpus" / "source.txt").write_text("Synthetic source.", encoding="utf-8")
    return workspace


def run_directory(workspace: Path, run_id: str = RUN_ID) -> Path:
    return workspace / ".soulkiller-local" / "evaluation" / run_id


def complete_frame(payload: bytes) -> bytes:
    """Construct the specified format independently of the production encoder."""
    return (
        b"SKRUN01\n" + struct.pack("!Q", len(payload)) + hashlib.sha256(payload).digest() + payload
    )


def directory_entries(path: Path) -> set[str]:
    return {entry.name for entry in path.iterdir()}


def assert_descriptors_closed(descriptors: list[int]) -> None:
    """Check ownership release without relying on a platform-wide FD count."""
    for descriptor in descriptors:
        try:
            os.fstat(descriptor)
        except OSError as error:
            assert error.errno == errno.EBADF
        else:
            raise AssertionError("A run-store descriptor was not closed.")


def track_descriptors(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    """Keep capability registration consistent while observing real acquisitions."""
    descriptors: list[int] = []
    original_open = os.open
    original_dup = os.dup

    def tracked_open(path: str, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        descriptor = original_open(path, flags, mode, dir_fd=dir_fd)
        descriptors.append(descriptor)
        return descriptor

    def tracked_dup(descriptor: int) -> int:
        duplicate = original_dup(descriptor)
        descriptors.append(duplicate)
        return duplicate

    monkeypatch.setattr(os, "open", tracked_open)
    monkeypatch.setattr(os, "dup", tracked_dup)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {tracked_open})
    return descriptors
