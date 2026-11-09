"""Strict mechanical response validation; this does not prove semantic support."""

import re

from .answer_result import AnswerResult
from .dialogue_constants import MAX_ANSWER_CODE_POINTS, MAX_COMPLETION_BYTES
from .dialogue_error import DialogueError
from .model_completion import ModelCompletion
from .saved_json import decode_saved
from .source_match import SourceMatch


def accept_completion(
    completion: ModelCompletion, sources: tuple[SourceMatch, ...]
) -> AnswerResult:
    """Reject malformed, non-final or fabricated citations before any trusted presentation."""
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
    allowed = {f"S{index}" for index in range(1, len(sources) + 1)}
    if (
        len(citations) != len(set(citations))
        or not set(citations) <= allowed
        or set(re.findall(r"\[(S[^\]\r\n]*)\]", text)) != set(citations)
        or status == "answer"
        and not citations
        or status == "conflict"
        and len(citations) < 2
    ):
        raise DialogueError("invalid_model_citations")
    return AnswerResult(status, text, tuple(citations), sources, completion.backend)
