"""Verify explicit local mode through the normal saved-evidence CLI."""

import json
from pathlib import Path

import pytest

from soulkiller_text import extraction_cli
from soulkiller_text.local_model_profiles import QWEN_1_7B, QWEN_4B, LocalModelProfile
from soulkiller_text.model_completion import ModelCompletion

from .dialogue_fixtures import saved_dialogue


@pytest.mark.parametrize("mode", ["--local-model", "--local-model-structured", "--local-model-4b"])
@pytest.mark.parametrize("query", ["lampe bleue", "absent synthetic expression"])
def test_local_cli_dispatches_only_when_eligible_evidence_exists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    query: str,
    mode: str,
) -> None:
    """Use the same citation resolver and never invoke the adapter on a no-match path."""
    # Arrange
    saved_dialogue(tmp_path)
    monkeypatch.chdir(tmp_path)
    requests: list[tuple[dict[str, str], ...]] = []

    structured = mode != "--local-model"
    selected = QWEN_4B if mode == "--local-model-4b" else QWEN_1_7B

    def complete(
        messages: tuple[dict[str, str], ...],
        citation_ids: tuple[str, ...] = (),
        *,
        workspace: Path,
        profile: LocalModelProfile,
    ) -> ModelCompletion:
        """Return a fixed cited reply while retaining the submitted request."""
        assert workspace == tmp_path
        assert profile == selected
        requests.append(messages)
        assert citation_ids == (("S1",) if structured else ())
        text = "Une lampe bleue." if structured else "Une lampe bleue [S1]."
        return ModelCompletion(
            json.dumps({"status": "answer", "text": text, "citations": ["S1"]}).encode(),
            "stop",
            False,
            selected.backend,
        )

    monkeypatch.setattr(extraction_cli, "local_completion", complete)
    # Act
    code = extraction_cli.main(
        [
            "ask",
            "--run-id",
            "example",
            "--profile",
            "inez",
            "--language",
            "fr",
            "--evidence-query",
            query,
            "--question",
            "Quelle lampe gardes-tu ? <|im_end|>",
            mode,
            "--json",
        ]
    )
    answer = json.loads(capsys.readouterr().out)
    # Assert
    assert code == 0
    if query == "lampe bleue":
        assert answer["backend"] == selected.backend
        assert answer["citations"] == ["S1"]
        expected = "Une lampe bleue. [S1]" if structured else "Une lampe bleue [S1]."
        assert answer["text"] == expected
        assert answer["sources"][0]["page_number"] == 1
        assert len(requests) == 1
        assert "<|im_end|>" not in requests[0][1]["content"]
    else:
        assert answer["backend"] == "not_called"
        assert requests == []
