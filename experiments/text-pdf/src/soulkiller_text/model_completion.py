"""Transport observations supplied by an explicit model collaborator."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelCompletion:
    """The adapter owns finality/tool flags; model-authored JSON cannot certify them."""

    payload: bytes
    finish_reason: str
    requested_tools: bool
