"""Run one grounded prompt with the pinned offline model."""

import sys
import time
from pathlib import Path
from typing import Any

from .dialogue_error import DialogueError
from .local_model_asset import verified_model
from .local_model_budget import local_deadline, require_local_budget
from .local_model_constants import CONTEXT_TOKENS, LOCAL_BACKEND, MODEL_ALIAS, OUTPUT_TOKENS, SEED
from .local_server_http import server_request
from .local_server_identity import require_owned_listener
from .local_server_process import owned_server, require_running
from .model_completion import ModelCompletion

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"enum": ["answer", "uncertain", "conflict"]},
        "text": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["status", "text", "citations"],
    "additionalProperties": False,
}


def _wait_ready(pid: int) -> None:
    """Wait under the outer deadline for the owned process and expected model alias."""
    while True:
        require_running(pid)
        health = server_request("/health")
        if health is not None:
            require_running(pid)
            if health.get("status") != "ok":
                raise DialogueError("invalid_local_model_health")
            break
        time.sleep(0.1)
    models = server_request("/v1/models") or {}
    entries = models.get("data")
    if (
        type(entries) is not list
        or len(entries) != 1
        or type(entries[0]) is not dict
        or entries[0].get("id") != MODEL_ALIAS
    ):
        raise DialogueError("unexpected_local_model")


def _prompt_tokens(messages: tuple[dict[str, str], ...]) -> list[int]:
    """Verify Qwen's non-thinking template and tokenize the exact completion input."""
    template = (
        server_request(
            "/apply-template",
            {"messages": messages, "chat_template_kwargs": {"enable_thinking": False}},
        )
        or {}
    )
    prompt = template.get("prompt")
    if type(prompt) is not str or not prompt.endswith("<think>\n\n</think>\n\n"):
        raise DialogueError("unexpected_local_model_template")
    tokenized = (
        server_request("/tokenize", {"content": prompt, "add_special": True, "parse_special": True})
        or {}
    )
    tokens = tokenized.get("tokens")
    if (
        type(tokens) is not list
        or not tokens
        or any(type(token) is not int or token < 0 for token in tokens)
    ):
        raise DialogueError("invalid_local_model_tokens")
    if len(tokens) + OUTPUT_TOKENS > CONTEXT_TOKENS:
        raise DialogueError("local_model_context_exceeded")
    return tokens


def _checked_completion(fields: dict[str, Any], token_count: int) -> ModelCompletion:
    """Accept only a complete bounded generation for the selected model and exact input."""
    count, predicted = fields.get("tokens_evaluated"), fields.get("tokens_predicted")
    if (
        fields.get("model") != MODEL_ALIAS
        or type(count) is not int
        or count != token_count
        or type(predicted) is not int
        or not 0 < predicted <= OUTPUT_TOKENS
        or fields.get("truncated") is not False
    ):
        raise DialogueError("invalid_local_model_usage")
    if fields.get("stop_type") != "eos":
        raise DialogueError("local_model_generation_incomplete")
    content = fields.get("content")
    if type(content) is not str:
        raise DialogueError("invalid_local_model_content")
    try:
        return ModelCompletion(content.encode(), "stop", False, LOCAL_BACKEND)
    except UnicodeError:
        raise DialogueError("invalid_local_model_content") from None


def _generate(tokens: list[int]) -> ModelCompletion:
    """Send one non-streaming, schema-constrained completion using the checked token IDs."""
    started = time.monotonic()
    fields = (
        server_request(
            "/completion",
            {
                "prompt": tokens,
                "n_predict": OUTPUT_TOKENS,
                "temperature": 0,
                "seed": SEED,
                "cache_prompt": False,
                "stream": False,
                "json_schema": RESPONSE_SCHEMA,
            },
        )
        or {}
    )
    count = fields.get("tokens_predicted")
    if type(count) is int and 0 < count <= OUTPUT_TOKENS:
        print(
            f"Local model generation: {time.monotonic() - started:.3f} s; "
            f"{len(tokens)} prompt tokens; {count} output tokens.",
            file=sys.stderr,
        )
    return _checked_completion(fields, len(tokens))


def local_completion(messages: tuple[dict[str, str], ...], *, workspace: Path) -> ModelCompletion:
    """Generate under the offline container limits, releasing the child on every exit."""
    require_local_budget()
    with verified_model(workspace) as descriptor:
        starting = time.monotonic()
        with owned_server(descriptor) as pid, local_deadline():
            _wait_ready(pid)
            require_owned_listener(pid)
            print(f"Local model startup: {time.monotonic() - starting:.3f} s.", file=sys.stderr)
            tokens = _prompt_tokens(messages)
            require_running(pid)
            require_owned_listener(pid)
            result = _generate(tokens)
            require_running(pid)
            return result
