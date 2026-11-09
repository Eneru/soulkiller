"""Loopback response handling tests with small deterministic wire responses."""

import socket
import threading

import pytest

from soulkiller_text import local_server_http
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.local_model_constants import SERVER_HOST


@pytest.mark.parametrize(
    ("headers", "body", "error"),
    [
        (b"200 OK\r\nContent-Length: 15\r\n", b'{"status":"ok"}', None),
        (b"302 Found\r\nLocation: https://example.invalid\r\n", b"", "local_model_http_rejected"),
        (b"200 OK\r\nContent-Length: 65537\r\n", b"", "local_model_response_too_large"),
        (b"200 OK\r\nContent-Length: 20\r\n", b'{"status":"ok"}', "local_model_transport_error"),
        (b"200 OK\r\nContent-Length: 13\r\n", b'{"x":1,"x":2}', "invalid_local_model_envelope"),
        (b"200 OK\r\nTransfer-Encoding: chunked\r\n", b"", "local_model_http_rejected"),
    ],
)
def test_loopback_responses_fail_closed(
    monkeypatch: pytest.MonkeyPatch, headers: bytes, body: bytes, error: str | None
) -> None:
    """Exercise the real HTTP parser with redirected, oversized and ambiguous responses."""
    # Arrange
    with socket.socket() as listener:
        listener.bind((SERVER_HOST, 0))
        listener.listen()
        listener.settimeout(2)
        monkeypatch.setattr(local_server_http, "SERVER_PORT", listener.getsockname()[1])

        def reply() -> None:
            """Send exactly one fixture response and close the only connection."""
            conn, _address = listener.accept()
            with conn:
                conn.settimeout(2)
                with conn.makefile("rb") as request:
                    while request.readline() not in (b"\r\n", b""):
                        pass
                conn.sendall(
                    b"HTTP/1.1 " + headers + b"Content-Type: application/json\r\n\r\n" + body
                )

        worker = threading.Thread(target=reply)
        worker.start()
        # Act / Assert
        try:
            if error is None:
                assert local_server_http.server_request("/health") == {"status": "ok"}
            else:
                with pytest.raises(DialogueError, match=error):
                    local_server_http.server_request("/health")
        finally:
            worker.join(timeout=3)
        assert not worker.is_alive()
