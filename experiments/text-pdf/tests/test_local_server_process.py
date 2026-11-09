"""Exercise ownership, occupied endpoints and cleanup without model weights."""

import os
import socket
from pathlib import Path

import pytest

from soulkiller_text import local_server_process as server
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.local_model_constants import SERVER_HOST
from soulkiller_text.local_model_profiles import QWEN_4B


def test_owned_child_is_reaped_after_interruption(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Launch a fixed sleeping test process and reclaim it when the caller interrupts."""
    # Arrange
    monkeypatch.setattr(server, "SERVER_PORT", 0)
    monkeypatch.setattr(server, "_command", lambda _descriptor, _alias: ("/usr/bin/sleep", "30"))
    model = tmp_path / "synthetic-model"
    model.write_bytes(b"test")

    # Act
    with model.open("rb") as stream, pytest.raises(KeyboardInterrupt):
        with server.owned_server(stream.fileno(), QWEN_4B.alias) as pid:
            server.require_running(pid)
            raise KeyboardInterrupt

    # Assert
    with pytest.raises(ChildProcessError):
        os.waitpid(pid, os.WNOHANG)


def test_occupied_endpoint_does_not_start_child(monkeypatch: pytest.MonkeyPatch) -> None:
    """Refuse an unrelated TCP listener while leaving it intact."""
    # Arrange
    with socket.socket() as listener:
        listener.bind((SERVER_HOST, 0))
        listener.listen()
        monkeypatch.setattr(server, "SERVER_PORT", listener.getsockname()[1])

        # Act / Assert
        with pytest.raises(DialogueError, match="local_model_endpoint_unavailable"):
            with server.owned_server(-1, QWEN_4B.alias):
                pytest.fail("occupied endpoint was reused")
        assert listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) == 1


def test_listener_must_belong_to_expected_process(monkeypatch: pytest.MonkeyPatch) -> None:
    """Compare the actual kernel listener inode with the expected process's descriptors."""
    # Arrange
    from soulkiller_text import local_server_identity

    with socket.socket() as listener:
        listener.bind((SERVER_HOST, 0))
        listener.listen()
        monkeypatch.setattr(local_server_identity, "SERVER_PORT", listener.getsockname()[1])

        # Act / Assert
        local_server_identity.require_owned_listener(os.getpid())
        with pytest.raises(DialogueError, match="local_model_endpoint_unavailable"):
            local_server_identity.require_owned_listener(-1)
