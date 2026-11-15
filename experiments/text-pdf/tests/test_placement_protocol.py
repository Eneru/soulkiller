"""Reject transport failures before model-authored data reaches the answer renderer."""

from pathlib import Path

import pytest

from soulkiller_text import placement_client, placement_worker
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.extraction_cli import main
from soulkiller_text.placement_protocol import FRAME_BYTES, read_reply
from soulkiller_text.worker_limits import WorkerLimits

from .dialogue_fixtures import saved_dialogue


@pytest.mark.parametrize(
    "frame",
    [
        b"",
        b" " * (FRAME_BYTES + 1),
        b'{"version":1,"completion":{}',
        b'{"version":1,"completion":{}}\n',
        b'{"version":2,"completion":{}}',
        b'{"version":true,"completion":{}}',
        b'{"version":1,"version":1,"completion":{}}',
        b'{"version":1,"completion":[]}',
    ],
)
def test_reply_frame_rejects_invalid_bytes(frame: bytes) -> None:
    """Reject malformed, oversized and differently versioned responses."""
    with pytest.raises(DialogueError, match="invalid_placement_worker_reply"):
        read_reply(frame)


@pytest.mark.parametrize(
    ("script", "error"),
    [
        ("import time; time.sleep(30)", "placement_worker_timeout"),
        (
            "import sys; sys.stdout.write('x' * 65537); sys.stdout.flush()",
            "placement_worker_failed",
        ),
        (
            """print('{"version":1,"completion":{"status":"answer","text":"Fake","""
            """"citations":["S9"]}}', end='')""",
            "invalid_model_citations",
        ),
    ],
)
def test_failed_child_yields_no_answer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    script: str,
    error: str,
) -> None:
    """Exercise the actual supervisor and local output rejection through the CLI."""
    saved_dialogue(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(placement_client, "BOOTSTRAP", script)
    if error == "placement_worker_timeout":
        monkeypatch.setattr(
            placement_client,
            "SIMULATION_LIMITS",
            WorkerLimits(wall_seconds=0.2, output_bytes=FRAME_BYTES),
        )

    status = main(
        [
            "ask",
            "--run-id",
            "example",
            "--profile",
            "inez",
            "--question",
            "Quelle lampe gardes-tu ?",
            "--evidence-query",
            "lampe bleue",
            "--language",
            "fr",
            "--simulate-remote",
        ]
    )

    output = capsys.readouterr()
    assert status == 1
    assert error in output.err
    assert output.out == ""


def test_worker_rejects_unapproved_request(
    monkeypatch: pytest.MonkeyPatch,
    capsysbinary: pytest.CaptureFixture[bytes],
) -> None:
    """An independently called worker rejects unknown request bytes without printing them."""
    from io import BytesIO, TextIOWrapper

    with TextIOWrapper(BytesIO(b'{"version":2}')) as stream:
        monkeypatch.setattr("sys.stdin", stream)

        status = placement_worker.main()

    output = capsysbinary.readouterr()
    assert status == 1
    assert output.out == output.err == b""
