"""Process observations tolerate init reaping a synthetic probe during a read."""

from pathlib import Path

import pytest

from .worker_process_helpers import process_is_stopped


def test_child_disappearing_during_proc_read_is_stopped(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    def vanished(path: Path, encoding: str) -> str:
        raise ProcessLookupError("synthetic child was already reaped")

    monkeypatch.setattr(Path, "read_text", vanished)
    # Act
    stopped = process_is_stopped(12345)
    # Assert
    assert stopped is True
