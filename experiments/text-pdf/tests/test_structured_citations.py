"""Exercise independent mechanical checks for the paired response contracts."""

import pytest

from soulkiller_text.answer_response import accept_completion
from soulkiller_text.dialogue_error import DialogueError
from soulkiller_text.source_search import search_evidence

from .dialogue_fixtures import completion
from .source_search_fixtures import text_row


@pytest.mark.parametrize(
    ("structured", "text", "ids", "status", "detail"),
    [
        (True, "I keep a lamp.", ["S9"], "answer", "out_of_scope_ids"),
        (True, "I keep a lamp.", ["S1", "S1"], "answer", "duplicate_ids"),
        (True, "I keep a lamp.", [], "answer", "missing_required_ids"),
        (True, "The sources disagree.", ["S1"], "conflict", "missing_required_ids"),
        (True, "I keep a lamp. [S1]", ["S1"], "answer", "model_authored_markers"),
        (True, "I keep a lamp. [ s1 ]", ["S1"], "answer", "model_authored_markers"),
        (False, "I keep a lamp.", ["S1"], "answer", "inline_id_mismatch"),
    ],
)
def test_citation_failures_disclose_only_fixed_details(
    structured: bool, text: str, ids: list[str], status: str, detail: str
) -> None:
    """Reject the cited answer without exposing its text or an invented reference."""
    # Arrange
    row = text_row("evidence")
    sources = search_evidence(None, (row.specification,), (row,), "evidence").matches
    reply = completion({"status": status, "text": text, "citations": ids})
    # Act
    with pytest.raises(DialogueError, match="^invalid_model_citations$") as caught:
        accept_completion(reply, sources, structured=structured)
    # Assert
    assert caught.value.detail == detail


def test_structured_uncertainty_can_omit_citations() -> None:
    """Preserve a complete abstention without synthesizing any references."""
    # Arrange
    row = text_row("evidence")
    sources = search_evidence(None, (row.specification,), (row,), "evidence").matches
    reply = completion({"status": "uncertain", "text": "I do not know.", "citations": []})
    # Act
    answer = accept_completion(reply, sources, structured=True)
    # Assert
    assert answer.status == "uncertain"
    assert answer.text == "I do not know."
    assert answer.citations == ()


def test_structured_conflict_renders_both_eligible_citations() -> None:
    """Resolve two distinct matches and append the application-owned markers in reply order."""
    # Arrange
    row = text_row("evidence then evidence")
    sources = search_evidence(None, (row.specification,), (row,), "evidence").matches
    reply = completion(
        {"status": "conflict", "text": "The sources disagree.", "citations": ["S2", "S1"]}
    )
    # Act
    answer = accept_completion(reply, sources, structured=True)
    # Assert
    assert answer.status == "conflict"
    assert answer.text == "The sources disagree. [S2] [S1]"
    assert answer.sources == sources
    assert answer.citations == ("S2", "S1")
