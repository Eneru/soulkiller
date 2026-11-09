"""Independent invented saved runs and recording model collaborators."""

import json
import shutil
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

from soulkiller_text.dialogue import Model
from soulkiller_text.dialogue_constants import DIALOGUE_CORPUS
from soulkiller_text.fixture_record import encode_fixture_record
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.load_corpus import load_corpus
from soulkiller_text.loaded_fixture import LoadedFixture
from soulkiller_text.model_completion import ModelCompletion
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.run_status import RunStatus
from soulkiller_text.run_store import create_run_store
from soulkiller_text.saved_run_writer import manifest_payload
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

Messages = tuple[dict[str, str], ...]


def completion(fields: object) -> ModelCompletion:
    """Construct a test transport observation independently of the response parser."""
    return ModelCompletion(json.dumps(fields).encode(), "stop", False)


def recording_model(reply: ModelCompletion) -> tuple[Model, list[Messages]]:
    """Return a fresh recording collaborator without network or generation."""
    calls: list[Messages] = []

    def respond(messages: Messages) -> ModelCompletion:
        """Capture the exact application request, then return the independently supplied reply."""
        calls.append(messages)
        return reply

    return respond, calls


def _saved_row(fixture: LoadedFixture) -> FixtureRun:
    """Build a complete independent TXT or literal-page observation for a single fixture."""
    spec = fixture.specification
    result: WorkerResult | PdfWorkerResult
    if spec.format == "pdf":
        result = PdfWorkerResult(
            PdfWorkerOutcome.SUCCESS,
            spec.sha256,
            (PdfPage(1, "Je garde une lampe bleue."), PdfPage(2, "Je garde une lampe rouge.")),
            2,
            (),
        )
    else:
        result = WorkerResult(WorkerOutcome.SUCCESS, spec.sha256, fixture.source.decode())
    return FixtureRun(spec, result, 1)


def saved_dialogue(
    workspace: Path,
    *,
    status: RunStatus | None = RunStatus.COMPLETE,
    omit: str | None = None,
    change: Callable[[FixtureRun], FixtureRun] | None = None,
    corrupt_excluded: bool = False,
    relabel_letter: bool = False,
) -> None:
    """Persist an independently declared extraction observation, with optional boundary faults."""
    source = Path(__file__).resolve().parents[1] / "examples/persona-inez"
    shutil.copytree(source, workspace / DIALOGUE_CORPUS)
    fixtures = tuple(
        fixture
        for fixture in load_corpus(workspace, DIALOGUE_CORPUS)
        if fixture.specification.fixture_id != omit
    )
    if relabel_letter:
        fixtures = tuple(
            replace(fixture, specification=replace(fixture.specification, subject_label="Inez"))
            if fixture.specification.fixture_id == "shared-letter"
            else fixture
            for fixture in fixtures
        )
    with create_run_store(workspace, DIALOGUE_CORPUS, "example") as store:
        store.write_record("manifest", manifest_payload(fixtures))
        for index, fixture in enumerate(fixtures, start=1):
            row = _saved_row(fixture)
            if change is not None:
                row = change(row)
            payload = encode_fixture_record(row)
            if corrupt_excluded and fixture.specification.fixture_id == "other-persona":
                payload = b"{}"
            store.write_record(f"fixture-{index:03}", payload)
        if status is not None:
            store.write_record(
                "summary",
                json.dumps(
                    {
                        "version": 1,
                        "status": status.value,
                        "output_bytes": len(fixtures),
                    }
                ).encode(),
            )
