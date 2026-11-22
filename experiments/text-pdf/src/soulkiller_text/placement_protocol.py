"""One bounded, canonical JSON frame per stream, terminated by EOF."""

from hashlib import sha256
from typing import cast

from .dialogue import Messages
from .dialogue_error import DialogueError
from .model_completion import ModelCompletion
from .placement_cases import CASES
from .saved_json import decode_saved, encode_saved

FRAME_BYTES = 64 * 1024
VERSION = 1
SIMULATED_BACKEND = "simulated_placement_worker"
INVALID_REPLY = "invalid_placement_worker_reply"


def request_frame(messages: Messages, ids: tuple[str, ...], expected: str | None) -> bytes:
    """Permit only the exact reviewed outbound bytes, including the extracted snippets."""
    frame = encode_saved({"version": VERSION, "messages": messages, "citation_ids": ids})
    if len(frame) > FRAME_BYTES or expected is None or sha256(frame).hexdigest() != expected:
        raise DialogueError("unapproved_placement_prompt")
    return frame


def simulated_reply(frame: bytes) -> bytes:
    """Accept a reviewed frame by digest and return its fixed, versioned response."""
    if not 0 < len(frame) <= FRAME_BYTES:
        raise DialogueError("unapproved_placement_prompt")
    digest = sha256(frame).hexdigest()
    for approved, (status, text, citations) in CASES.values():
        if digest == approved:
            completion = {"status": status, "text": text, "citations": citations}
            return encode_saved({"version": VERSION, "completion": completion})
    raise DialogueError("unapproved_placement_prompt")


def read_reply(frame: bytes) -> ModelCompletion:
    """Reject foreign versions, trailing output and invalid framing before local citation checks."""
    if not 0 < len(frame) <= FRAME_BYTES:
        raise DialogueError(INVALID_REPLY)
    try:
        fields = decode_saved(frame)
        if (
            set(fields) != {"version", "completion"}
            or type(fields["version"]) is not int
            or fields["version"] != VERSION
            or type(fields["completion"]) is not dict
            or encode_saved(fields) != frame
        ):
            raise ValueError(INVALID_REPLY)
        payload = encode_saved(fields["completion"])
    except ValueError:
        raise DialogueError(INVALID_REPLY) from None
    return ModelCompletion(payload, "stop", False, SIMULATED_BACKEND)


def reviewed_request(frame: bytes) -> tuple[Messages, tuple[str, ...]]:
    """Decode only the exact versioned bytes whose digest matches a reviewed case."""
    if not 0 < len(frame) <= FRAME_BYTES:
        raise DialogueError("unapproved_placement_prompt")
    digest = sha256(frame).hexdigest()
    if not any(digest == approved for approved, _ in CASES.values()):
        raise DialogueError("unapproved_placement_prompt")
    # The digest binds the complete canonical structure, including field types.
    fields = decode_saved(frame)
    messages = tuple(cast(list[dict[str, str]], fields["messages"]))
    ids = tuple(cast(list[str], fields["citation_ids"]))
    return messages, ids
