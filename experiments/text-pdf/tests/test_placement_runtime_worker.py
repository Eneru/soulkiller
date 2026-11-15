"""Exercise the real worker protocol without depending on weights or credentials."""

import sys
from io import BytesIO, TextIOWrapper
from pathlib import Path
from typing import Never

import pytest

from soulkiller_text import placement_runtime_worker as worker
from soulkiller_text.dialogue import Messages, ask_saved
from soulkiller_text.dialogue_constants import DIALOGUE_CORPUS
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.local_model import RuntimeObservation
from soulkiller_text.local_model_profiles import QWEN_4B, LocalModelProfile
from soulkiller_text.model_completion import ModelCompletion
from soulkiller_text.placement_client import approved_prompt
from soulkiller_text.placement_protocol import request_frame
from soulkiller_text.saved_json import decode_saved

from .dialogue_fixtures import saved_dialogue


@pytest.fixture
def conflict_request(tmp_path: Path) -> bytes:
    """Capture the exact conflict prompt emitted by the normal saved-dialogue path."""
    saved_dialogue(tmp_path)
    question = "De quelle couleur est ta lampe ?"
    expected = approved_prompt(DIALOGUE_CORPUS, "fr", "lampe", question)
    captured: list[bytes] = []

    def capture(messages: Messages, ids: tuple[str, ...]) -> ModelCompletion:
        """Record the frame and return an independent structured completion."""
        captured.append(request_frame(messages, ids, expected))
        return ModelCompletion(
            b'{"status":"uncertain","text":"Je ne sais pas.","citations":[]}', "stop", False
        )

    ask_saved(
        tmp_path,
        DIALOGUE_CORPUS,
        "example",
        "inez",
        question,
        "lampe",
        "fr",
        None,
        structured_model=capture,
    )
    return captured[0]


@pytest.fixture
def worker_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Supply synthetic cgroup readings while keeping the kernel test independent."""
    cgroup = tmp_path / "cgroup"
    cgroup.mkdir()
    (cgroup / "memory.peak").write_text("2500000000")
    (cgroup / "memory.swap.max").write_text("0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(worker, "CGROUP_ROOT", cgroup)
    monkeypatch.setattr(worker, "require_local_budget", lambda: None)
    return cgroup


def test_worker_emits_pinned_response_and_numeric_observations(
    tmp_path: Path,
    conflict_request: bytes,
    worker_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfdbinary: pytest.CaptureFixture[bytes],
) -> None:
    """Verify real stdio framing with an independent CPU runtime double."""
    calls: list[tuple[Messages, tuple[str, ...]]] = []

    def infer(
        messages: Messages,
        ids: tuple[str, ...],
        *,
        workspace: Path,
        profile: LocalModelProfile,
        observe: RuntimeObservation,
    ) -> ModelCompletion:
        """Check the pinned inputs and deliver one synthetic completion with measurements."""
        assert workspace == tmp_path
        assert profile is QWEN_4B
        calls.append((messages, ids))
        observe("startup", 100, 0, 0)
        observe("generation", 200, 222, 40)
        return ModelCompletion(
            b'{"status":"conflict","text":"The lamp colour is disputed.","citations":["S1","S2"]}',
            "stop",
            False,
        )

    monkeypatch.setattr(worker, "complete_under_deadline", infer)
    with TextIOWrapper(BytesIO(conflict_request)) as stream:
        monkeypatch.setattr(sys, "stdin", stream)

        status = worker.main()

    output = capfdbinary.readouterr()
    assert status == 0
    assert output.err == b""
    assert len(calls) == 1
    assert calls[0][1] == ("S1", "S2")
    assert decode_saved(output.out) == {
        "version": 1,
        "completion": {
            "status": "conflict",
            "text": "The lamp colour is disputed.",
            "citations": ["S1", "S2"],
        },
        "metrics": {
            "startup_ms": 100,
            "generation_ms": 200,
            "prompt_tokens": 222,
            "completion_tokens": 40,
            "memory_peak_bytes": 2500000000,
        },
    }


@pytest.mark.parametrize("invalid", ["swap", "network", "prompt"])
def test_worker_rejects_unreviewed_input_and_environment(
    conflict_request: bytes,
    worker_environment: Path,
    monkeypatch: pytest.MonkeyPatch,
    capfdbinary: pytest.CaptureFixture[bytes],
    invalid: str,
) -> None:
    """Block model startup before reading or generating from ineligible requests."""
    frame = conflict_request + b" " if invalid == "prompt" else conflict_request

    def fail_inference(*_args: object, **_kwargs: object) -> Never:
        """Prohibit runtime launch for the ineligible case."""
        pytest.fail("runtime must not start")

    def connected() -> Never:
        """Represent the connected-container guard failure."""
        raise DialogueError("local_model_container_limits_required")

    monkeypatch.setattr(worker, "complete_under_deadline", fail_inference)
    if invalid == "network":
        monkeypatch.setattr(worker, "require_local_budget", connected)
    if invalid == "swap":
        (worker_environment / "memory.swap.max").write_text("1")
    with TextIOWrapper(BytesIO(frame)) as stream:
        monkeypatch.setattr(sys, "stdin", stream)

        status = worker.main()

    output = capfdbinary.readouterr()
    assert status == 1
    assert output.out == output.err == b""
