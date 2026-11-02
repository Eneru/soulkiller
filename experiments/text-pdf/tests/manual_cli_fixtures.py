"""Reusable synthetic setups for the manual saved-run journey."""

from importlib import import_module
from pathlib import Path

import pytest

from soulkiller_text.corpus_fixture import CorpusFixture
from soulkiller_text.text_annotation import TextAnnotation

from .corpus_run_fixtures import (
    WorkerCall,
    ordered_text_corpus,
    permit_scheduling,
    recording_workers,
)


def prepare_run(
    workspace: Path, monkeypatch: pytest.MonkeyPatch, *, fault: BaseException | None = None
) -> list[WorkerCall]:
    """Allow scheduler unit tests only, retaining real metadata validation and store I/O."""
    ordered_text_corpus(workspace)
    permit_scheduling(monkeypatch)
    module = import_module("soulkiller_text.saved_run")
    monkeypatch.setattr(module, "has_offline_topology", lambda: True)
    calls = recording_workers(monkeypatch, fault=fault)
    return calls


def text_reference() -> CorpusFixture:
    """Declare an accented, literal reference independently of candidate output."""
    return CorpusFixture(
        "text-fr",
        "notes.txt",
        "a" * 64,
        "txt",
        "fr",
        "Invented",
        "Invented",
        "success",
        (TextAnnotation(2, 6, "café"),),
    )
