"""Independent synthetic inputs and scheduling collaborators for corpus runs."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

import pytest

from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.synthetic_pdf import build_text_pdf
from soulkiller_text.worker_execution import WorkerExecution
from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .corpus_helpers import fixture_document
from .pdf_corpus_fixtures import pdf_document, write_evaluation_corpus

WorkerCall = tuple[str, bytes, WorkerLimits, int | None]


def ordered_text_corpus(workspace: Path, count: int = 3) -> Path:
    """Write IDs whose manifest order differs from sorted ID/path order."""
    ids = ("z-last", "a-first", "m-middle")[:count]
    entries = [fixture_document(name, f"{name}.txt") for name in ids]
    return write_evaluation_corpus(workspace, entries, {f"{name}.txt": b"abc" for name in ids})


def mixed_execution_corpus(workspace: Path) -> Path:
    """Include independent bilingual facts and failures before later valid files."""
    french = build_text_pdf(("Inez garde une lampe bleue.", "Une archive inventée."))
    english = build_text_pdf(("Corin collects paper stars.",))
    invalid = fixture_document("invalid-txt", "invalid.txt")
    invalid.update(
        {
            "sha256": hashlib.sha256(b"\xff").hexdigest(),
            "outcome": "invalid_encoding",
            "annotations": [],
        }
    )
    text = fixture_document("text-en", "notes.txt")
    fr_pdf = pdf_document("pdf-fr", "french.pdf", french)
    fr_pdf["annotations"] = [{"page_number": 1, "quote": "Inez garde une lampe bleue."}]
    malformed = pdf_document("malformed", "broken.pdf", b"not a PDF")
    malformed.update({"page_count": 1, "outcome": "malformed_input", "annotations": []})
    en_pdf = pdf_document("pdf-en", "english.pdf", english)
    en_pdf.update(
        {
            "language": "en",
            "page_count": 1,
            "annotations": [{"page_number": 1, "quote": "Corin collects paper stars."}],
        }
    )
    return write_evaluation_corpus(
        workspace,
        [invalid, text, fr_pdf, malformed, en_pdf],
        {
            "invalid.txt": b"\xff",
            "notes.txt": b"abc",
            "french.pdf": french,
            "broken.pdf": b"not a PDF",
            "english.pdf": english,
        },
    )


def permit_scheduling(monkeypatch: pytest.MonkeyPatch, clock: list[float] | None = None) -> None:
    """Provide a controlled supported environment only for scheduler unit cases."""
    runner = import_module("soulkiller_text.corpus_runner")
    entry = import_module("soulkiller_text.run_corpus")
    values = [0.0] if clock is None else clock
    monkeypatch.setattr(runner, "has_offline_topology", lambda: True)
    monkeypatch.setattr(entry, "monotonic", lambda: values[0])


@dataclass
class WorkerScript:
    """One fresh scheduler collaborator with independently declared observations."""

    counts: tuple[int, ...]
    outcomes: tuple[WorkerOutcome | PdfWorkerOutcome, ...]
    clock: list[float] | None
    advances: tuple[float, ...]
    fault: BaseException | None
    fault_at: int
    on_call: Callable[[], None] | None
    calls: list[WorkerCall] = field(default_factory=list)

    def before_call(self, kind: str, source: bytes, limits: WorkerLimits, pages: int | None) -> int:
        index = len(self.calls)
        self.calls.append((kind, source, limits, pages))
        if self.on_call is not None:
            self.on_call()
        if self.clock is not None and index < len(self.advances):
            self.clock[0] += self.advances[index]
        if self.fault is not None and index == self.fault_at:
            raise self.fault
        return index

    def text_worker(self, source: bytes, limits: WorkerLimits) -> WorkerExecution[WorkerResult]:
        index = self.before_call("txt", source, limits, None)
        outcome = WorkerOutcome(self.outcomes[index]) if self.outcomes else WorkerOutcome.SUCCESS
        text = source.decode("utf-8") if outcome is WorkerOutcome.SUCCESS else None
        result = WorkerResult(outcome, hashlib.sha256(source).hexdigest(), text)
        return WorkerExecution(result, self.counts[index])

    def pdf_worker(
        self, source: bytes, limits: WorkerLimits, max_pages: int
    ) -> WorkerExecution[PdfWorkerResult]:
        index = self.before_call("pdf", source, limits, max_pages)
        outcome = (
            PdfWorkerOutcome(self.outcomes[index]) if self.outcomes else PdfWorkerOutcome.SUCCESS
        )
        pages = (
            (PdfPage(1, "Independent worker value"),) if outcome is PdfWorkerOutcome.SUCCESS else ()
        )
        total = 1 if pages else None
        result = PdfWorkerResult(outcome, hashlib.sha256(source).hexdigest(), pages, total, ())
        return WorkerExecution(result, self.counts[index])


def recording_workers(
    monkeypatch: pytest.MonkeyPatch,
    *,
    counts: tuple[int, ...] = (1, 1, 1),
    outcomes: tuple[WorkerOutcome | PdfWorkerOutcome, ...] = (),
    clock: list[float] | None = None,
    advances: tuple[float, ...] = (),
    fault: BaseException | None = None,
    fault_at: int = 1,
    on_call: Callable[[], None] | None = None,
) -> list[WorkerCall]:
    """Install one fresh script and return its append-only call observations."""
    script = WorkerScript(counts, outcomes, clock, advances, fault, fault_at, on_call)
    runner = import_module("soulkiller_text.corpus_runner")
    monkeypatch.setattr(runner, "run_observed_text_worker", script.text_worker)
    monkeypatch.setattr(runner, "run_observed_pdf_worker", script.pdf_worker)
    return script.calls
