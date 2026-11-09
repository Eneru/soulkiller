"""Offline model adapter tests using deterministic server replies."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from soulkiller_text import local_model
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.local_model_constants import CONTEXT_TOKENS, LOCAL_BACKEND, MODEL_ALIAS


@pytest.mark.parametrize(
    ("tokens", "citation_ids", "stop_type", "error"),
    [
        ([42, 7], (), "eos", None),
        ([42, 7], ("S1", "S2"), "eos", None),
        ([42] * CONTEXT_TOKENS, (), "eos", "local_model_context_exceeded"),
        ([True], (), "eos", "invalid_local_model_tokens"),
        ([42, 7], (), "limit", "local_model_generation_incomplete"),
    ],
)
def test_bounded_trial_uses_checked_tokens_and_reaps_on_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tokens: list[int],
    citation_ids: tuple[str, ...],
    stop_type: str,
    error: str | None,
) -> None:
    """Send the exact token IDs at most once, with cleanup on every outcome."""
    # Arrange
    calls: list[tuple[str, dict[str, Any] | None]] = []
    lifecycle = []

    @contextmanager
    def asset(_path: Path) -> Iterator[int]:
        """Expose one synthetic model descriptor for the call."""
        yield 5

    @contextmanager
    def child(descriptor: int) -> Iterator[int]:
        """Record the lifecycle without starting a real runtime."""
        assert descriptor == 5
        lifecycle.append("started")
        try:
            yield 123
        finally:
            lifecycle.append("reaped")

    def request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return the reviewed contract fields for each fixed request."""
        calls.append((path, payload))
        replies: dict[str, dict[str, Any]] = {
            "/health": {"status": "ok"},
            "/v1/models": {"data": [{"id": MODEL_ALIAS}]},
            "/apply-template": {"prompt": "prompt<think>\n\n</think>\n\n"},
            "/tokenize": {"tokens": tokens},
            "/completion": {
                "content": '{"status":"answer","text":"I know [S1].","citations":["S1"]}',
                "model": MODEL_ALIAS,
                "tokens_evaluated": len(tokens),
                "tokens_predicted": 17,
                "stop_type": stop_type,
                "truncated": False,
            },
        }
        return replies[path]

    monkeypatch.setattr(local_model, "verified_model", asset)
    monkeypatch.setattr(local_model, "owned_server", child)
    monkeypatch.setattr(local_model, "require_local_budget", lambda: None)
    monkeypatch.setattr(local_model, "require_running", lambda _pid: None)
    monkeypatch.setattr(local_model, "require_owned_listener", lambda _pid: None)
    monkeypatch.setattr(local_model, "server_request", request)
    messages = ({"role": "user", "content": "Synthetic question?"},)

    # Act / Assert
    if error is None:
        assert (
            local_model.local_completion(messages, citation_ids, workspace=tmp_path).backend
            == LOCAL_BACKEND
        )
    else:
        with pytest.raises(DialogueError, match=error):
            local_model.local_completion(messages, citation_ids, workspace=tmp_path)

    assert lifecycle == ["started", "reaped"]
    assert calls[2][1] == {"messages": messages, "chat_template_kwargs": {"enable_thinking": False}}
    completion_calls = [payload for path, payload in calls if path == "/completion"]
    if error in ("local_model_context_exceeded", "invalid_local_model_tokens"):
        assert completion_calls == []
    else:
        assert len(completion_calls) == 1
        completion = completion_calls[0]
        assert completion is not None
        assert completion["prompt"] == tokens
        assert completion["n_predict"] == 128
        assert completion["cache_prompt"] is False
        assert completion["stream"] is False
        items = completion["json_schema"]["properties"]["citations"]["items"]
        assert items == ({"enum": list(citation_ids)} if citation_ids else {"type": "string"})
