"""PDF classification reuses actual bounded child transfer and mandatory cleanup."""

from functools import partial

import pytest

from soulkiller_text import supervise
from soulkiller_text.pdf_worker_completion import classify_completion
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.supervise import run_command
from soulkiller_text.worker_limits import WorkerLimits

from .pdf_worker_fixtures import pdf_payload
from .synthetic_sources import BILINGUAL_BYTES, BILINGUAL_SHA256
from .worker_fixtures import blocking_command, flooding_command, responding_command, worker_command
from .worker_process_helpers import assert_reaped, record_processes


def test_pdf_response_uses_independent_classifier_and_reaps_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    command = responding_command(pdf_payload())
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert result.outcome is PdfWorkerOutcome.SUCCESS
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.pages[0].page_number == 1
    assert_reaped(processes)


@pytest.mark.parametrize(
    ("code", "expected"),
    [(1, "candidate_failure"), (3, "unsupported_environment"), (4, "resource_limit")],
)
def test_pdf_nonzero_exit_discards_apparent_page_evidence(code: int, expected: str) -> None:
    # Arrange
    command = responding_command(pdf_payload(), exit_code=code)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert result.outcome == expected
    assert result.pages == ()
    assert result.total_pages is None


@pytest.mark.parametrize("descriptor", [1, 2], ids=["stdout", "stderr"])
def test_pdf_combined_output_overflow_discards_evidence_and_reaps(
    descriptor: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)
    limits = WorkerLimits(wall_seconds=5, output_bytes=1024)
    # Act
    result = run_command(flooding_command(descriptor), BILINGUAL_BYTES, limits, classify_completion)
    # Assert
    assert result.outcome is PdfWorkerOutcome.OUTPUT_LIMIT
    assert result.pages == ()
    assert_reaped(processes)


def test_pdf_early_response_cannot_escape_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    payload = pdf_payload()
    command = worker_command(
        "import os,time\n"
        f"os.write(1, {payload!r})\n"
        "os.close(0)\nos.close(1)\nos.close(2)\ntime.sleep(60)\n"
    )
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(
        command, BILINGUAL_BYTES, WorkerLimits(wall_seconds=0.5), classify_completion
    )
    # Assert
    assert result.outcome is PdfWorkerOutcome.TIMEOUT
    assert result.pages == ()
    assert_reaped(processes)


@pytest.mark.parametrize(
    "payload",
    [
        b"not json",
        pdf_payload(source_sha256="0" * 64),
        pdf_payload() * 2,
        pdf_payload(outcome="timeout", pages=[], total_pages=None),
    ],
)
def test_pdf_inconsistent_wire_discards_all_unverified_page_evidence(payload: bytes) -> None:
    # Arrange
    command = responding_command(payload)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert result.outcome is PdfWorkerOutcome.PROTOCOL_ERROR
    assert result.source_sha256 == BILINGUAL_SHA256
    assert result.pages == ()
    assert result.total_pages is None
    assert result.missing_pages == ()


def test_pdf_declared_pages_are_checked_against_requested_budget() -> None:
    # Arrange
    payload = pdf_payload(
        pages=[{"page_number": 1, "text": "first"}, {"page_number": 2, "text": "second"}],
        total_pages=2,
    )
    command = responding_command(payload)
    classifier = partial(classify_completion, max_pages=1)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classifier)
    # Assert
    assert result.outcome is PdfWorkerOutcome.PROTOCOL_ERROR
    assert result.pages == ()


def test_pdf_launch_failure_uses_pdf_result_type_without_diagnostics() -> None:
    # Arrange
    command = ("/definitely-not-a-soulkiller-worker",)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert result.outcome is PdfWorkerOutcome.CANDIDATE_FAILURE
    assert result.pages == ()
    assert "definitely-not" not in repr(result)


def test_pdf_cancellation_propagates_only_after_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange
    processes = record_processes(monkeypatch)

    def cancelled(*args: object) -> tuple[None, bytes]:
        raise KeyboardInterrupt()

    monkeypatch.setattr(supervise, "capture_pipes", cancelled)
    # Act
    with pytest.raises(KeyboardInterrupt):
        run_command(blocking_command(), BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert_reaped(processes)


def test_actual_pdf_classifier_observes_reserved_allocation_failure() -> None:
    # Arrange
    command = worker_command(
        "import resource,sys\n"
        "sys.stdin.buffer.read()\n"
        "resource.setrlimit(resource.RLIMIT_AS,(64*1024**2,64*1024**2))\n"
        "try:\n    bytearray(128*1024**2)\n"
        "except MemoryError:\n    sys.exit(4)\n"
    )
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), classify_completion)
    # Assert
    assert result.outcome is PdfWorkerOutcome.RESOURCE_LIMIT
    assert result.pages == ()
    assert result.total_pages is None
