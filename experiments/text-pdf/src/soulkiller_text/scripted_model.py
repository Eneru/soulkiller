"""Explicit manual demo responses; these scripts do not interpret a question or run an LLM."""

import json

from .model_completion import ModelCompletion

SCRIPTS: dict[str, dict[str, tuple[str, str, list[str]]]] = {
    "lamp": {
        "fr": ("answer", "Je garde une lampe bleue. [S1]", ["S1"]),
        "en": ("answer", "I keep a blue lamp. [S1]", ["S1"]),
    },
    "conflict": {
        "fr": (
            "conflict",
            "Mes sources indiquent une lampe bleue [S1] et rouge [S2]. Je ne peux pas trancher.",
            ["S1", "S2"],
        ),
        "en": (
            "conflict",
            "My sources say blue [S1] and red [S2]. I cannot choose between them.",
            ["S1", "S2"],
        ),
    },
    "paper-stars": {
        "fr": ("answer", "Je collectionne des étoiles en papier. [S1]", ["S1"]),
        "en": ("answer", "I collect paper stars. [S1]", ["S1"]),
    },
    "third-party": {
        "fr": ("answer", "Corin collectionne des billes en verre. [S1]", ["S1"]),
        "en": ("answer", "Corin collects glass marbles. [S1]", ["S1"]),
    },
    "uncertain": {
        "fr": ("uncertain", "Je ne sais pas.", []),
        "en": ("uncertain", "I do not know.", []),
    },
}

DEMO_CASES = tuple(SCRIPTS)


def demo_completion(
    _messages: tuple[dict[str, str], ...], *, case: str, language: str
) -> ModelCompletion:
    """Return a selected script regardless of the question, for contract demonstrations only."""
    status, text, citations = SCRIPTS[case][language]
    payload = json.dumps({"status": status, "text": text, "citations": citations}).encode()
    return ModelCompletion(payload, "stop", False)
