"""Strict mechanical response validation; this does not prove semantic support."""

import re

from .answer_result import AnswerResult
from .dialogue_constants import MAX_ANSWER_CODE_POINTS, MAX_COMPLETION_BYTES
from .dialogue_error import DialogueError
from .model_completion import ModelCompletion
from .saved_json import decode_saved
from .source_match import SourceMatch

INLINE_MARKER = re.compile(r"\[(S[^\]\r\n]*)\]")


STRUCTURED_MARKER = re.compile(r"\[[ \t]*S[^\]\r\n]*\]", re.IGNORECASE)


def citation_ids(source_count: int) -> tuple[str, ...]:
    """Assign deterministic request-local IDs in saved passage order."""
    return tuple(f"S{index}" for index in range(1, source_count + 1))


def _response_fields(completion: ModelCompletion) -> tuple[str, str, list[str]]:
    """Check finality, the byte limit and the exact JSON fields before inspecting IDs."""
    if (
        type(completion) is not ModelCompletion
        or completion.finish_reason != "stop"
        or completion.requested_tools is not False
        or type(completion.payload) is not bytes
        or not 0 < len(completion.payload) <= MAX_COMPLETION_BYTES
    ):
        raise DialogueError("invalid_model_completion")
    try:
        fields = decode_saved(completion.payload)
    except ValueError:
        raise DialogueError("invalid_model_response") from None
    if set(fields) != {"status", "text", "citations"}:
        raise DialogueError("invalid_model_response")
    status, text, citations = fields["status"], fields["text"], fields["citations"]
    if (
        type(status) is not str
        or status not in ("answer", "uncertain", "conflict")
        or type(text) is not str
        or not text.strip()
        or len(text) > MAX_ANSWER_CODE_POINTS
        or type(citations) is not list
        or any(type(item) is not str for item in citations)
    ):
        raise DialogueError("invalid_model_response")
    return status, text, citations


def _citation_issue(
    status: str, text: str, ids: list[str], allowed: tuple[str, ...], *, structured: bool
) -> str | None:
    """Name the first mechanical rejection without including any model text."""
    if len(ids) != len(set(ids)):
        return "duplicate_ids"
    if not set(ids) <= set(allowed):
        return "out_of_scope_ids"
    if (status == "answer" and not ids) or (status == "conflict" and len(ids) < 2):
        return "missing_required_ids"
    if structured and STRUCTURED_MARKER.search(text):
        return "model_authored_markers"
    if not structured and set(INLINE_MARKER.findall(text)) != set(ids):
        return "inline_id_mismatch"
    return None


def accept_completion(
    completion: ModelCompletion, sources: tuple[SourceMatch, ...], *, structured: bool = False
) -> AnswerResult:
    """Validate references against supplied passages before rendering structured markers."""
    status, text, ids = _response_fields(completion)
    issue = _citation_issue(status, text, ids, citation_ids(len(sources)), structured=structured)
    if issue is not None:
        raise DialogueError("invalid_model_citations", detail=issue)
    if structured and ids:
        text = " ".join((text.rstrip(), *(f"[{citation}]" for citation in ids)))
    return AnswerResult(status, text, tuple(ids), sources, completion.backend)
