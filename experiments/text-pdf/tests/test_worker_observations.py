"""Actual transport observation remains independent of accepted worker evidence."""

import importlib
import json
import os
import subprocess
from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from soulkiller_text.pdf_worker import run_observed_pdf_worker
from soulkiller_text.pdf_worker_completion import classify_completion as classify_pdf_completion
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.run_text_worker import run_observed_text_worker
from soulkiller_text.supervise import run_command
from soulkiller_text.synthetic_pdf import build_text_pdf
from soulkiller_text.worker_cleanup_error import WorkerCleanupError
from soulkiller_text.worker_execution import WorkerExecution
from soulkiller_text.worker_limits import WorkerLimits
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_output_counter import WorkerOutputCounter
from soulkiller_text.worker_result import WorkerResult

from .pdf_worker_fixtures import externally_offline, pdf_payload
from .synthetic_sources import BILINGUAL_BYTES, BILINGUAL_SHA256, BILINGUAL_TEXT
from .worker_fixtures import flooding_command, responding_command, result_payload, worker_command
from .worker_process_helpers import assert_reaped, record_processes


def test_success_counts_wire_response_and_discarded_stderr_without_reconstruction() -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256)
    diagnostic = b"Invented diagnostic, absent from accepted text."
    counter = WorkerOutputCounter()
    command = responding_command(payload, stderr=diagnostic)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), output_observer=counter.observe)
    # Assert
    assert result.outcome is WorkerOutcome.SUCCESS
    assert result.text == "synthetic"
    assert counter.output_bytes == len(payload) + len(diagnostic)
    assert diagnostic.decode("ascii") not in repr(result)


def test_combined_output_at_exact_cap_retains_success_and_all_consumed_bytes() -> None:
    # Arrange
    payload = result_payload(BILINGUAL_SHA256)
    diagnostic = b"independent stderr"
    output_cap = len(payload) + len(diagnostic)
    counter = WorkerOutputCounter()
    limits = WorkerLimits(output_bytes=output_cap)
    # Act
    result = run_command(
        responding_command(payload, stderr=diagnostic),
        BILINGUAL_BYTES,
        limits,
        output_observer=counter.observe,
    )
    # Assert
    assert result.outcome is WorkerOutcome.SUCCESS
    assert counter.output_bytes == output_cap


@pytest.mark.parametrize("descriptor", [1, 2], ids=["stdout", "stderr"])
def test_output_overflow_counts_exactly_one_detection_byte_and_still_reaps(
    descriptor: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    limits = WorkerLimits(wall_seconds=5, output_bytes=1024)
    counter = WorkerOutputCounter()
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(
        flooding_command(descriptor),
        BILINGUAL_BYTES,
        limits,
        output_observer=counter.observe,
    )
    # Assert
    assert result.outcome is WorkerOutcome.OUTPUT_LIMIT
    assert counter.output_bytes == limits.output_bytes + 1
    assert_reaped(processes)


@pytest.mark.parametrize("exit_code", [0, 1], ids=["protocol-failure", "candidate-failure"])
def test_failed_response_keeps_actual_stdout_and_stderr_consumption(exit_code: int) -> None:
    # Arrange
    payload = b"synthetic invalid response"
    diagnostic = b"independent discarded stderr"
    counter = WorkerOutputCounter()
    command = responding_command(payload, exit_code=exit_code, stderr=diagnostic)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), output_observer=counter.observe)
    # Assert
    expected = WorkerOutcome.PROTOCOL_ERROR if exit_code == 0 else WorkerOutcome.CANDIDATE_FAILURE
    assert result.outcome is expected
    assert result.text is None
    assert counter.output_bytes == len(payload) + len(diagnostic)


def test_timeout_keeps_bytes_read_before_deadline_and_reaps_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    payload = b"incomplete synthetic response"
    diagnostic = b"deadline diagnostic"
    counter = WorkerOutputCounter()
    command = worker_command(
        "import os,sys,time\n"
        "sys.stdin.buffer.read()\n"
        f"os.write(1, {payload!r})\n"
        f"os.write(2, {diagnostic!r})\n"
        "os.close(1)\nos.close(2)\ntime.sleep(60)\n"
    )
    processes = record_processes(monkeypatch)
    # Act
    result = run_command(
        command, BILINGUAL_BYTES, WorkerLimits(wall_seconds=0.5), output_observer=counter.observe
    )
    # Assert
    assert result.outcome is WorkerOutcome.TIMEOUT
    assert counter.output_bytes == len(payload) + len(diagnostic)
    assert_reaped(processes)


def test_pdf_classifier_preserves_observation_of_its_distinct_wire_schema() -> None:
    # Arrange
    payload = pdf_payload()
    diagnostic = b"independent PDF diagnostic"
    counter = WorkerOutputCounter()
    # Act
    result = run_command(
        responding_command(payload, stderr=diagnostic),
        BILINGUAL_BYTES,
        WorkerLimits(),
        classify_pdf_completion,
        output_observer=counter.observe,
    )
    # Assert
    assert result.outcome is PdfWorkerOutcome.SUCCESS
    assert result.total_pages == 1
    assert counter.output_bytes == len(payload) + len(diagnostic)


def test_worker_with_no_output_does_not_notify_observer_on_pipe_eof() -> None:
    # Arrange
    chunks: list[int] = []
    command = responding_command(b"")
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), output_observer=chunks.append)
    # Assert
    assert result.outcome is WorkerOutcome.PROTOCOL_ERROR
    assert chunks == []


def test_failed_launch_has_zero_observed_transport_consumption() -> None:
    # Arrange
    counter = WorkerOutputCounter()
    command = ("/definitely-not-a-soulkiller-worker",)
    # Act
    result = run_command(command, BILINGUAL_BYTES, WorkerLimits(), output_observer=counter.observe)
    # Assert
    assert result.outcome is WorkerOutcome.CANDIDATE_FAILURE
    assert counter.output_bytes == 0


def test_real_observed_text_worker_retains_exact_independently_declared_wire_size() -> None:
    # Arrange
    expected_payload = json.dumps(
        {
            "version": 1,
            "outcome": "success",
            "source_sha256": BILINGUAL_SHA256,
            "text": BILINGUAL_TEXT,
        },
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    # Act
    execution = run_observed_text_worker(BILINGUAL_BYTES)
    # Assert
    assert execution.result.outcome is WorkerOutcome.SUCCESS
    assert execution.result.text == BILINGUAL_TEXT
    assert execution.output_bytes == len(expected_payload)


def test_real_observed_text_worker_retains_overflow_measurement_without_text() -> None:
    # Arrange
    limits = WorkerLimits(output_bytes=1)
    # Act
    execution = run_observed_text_worker(BILINGUAL_BYTES, limits)
    # Assert
    assert execution.result.outcome is WorkerOutcome.OUTPUT_LIMIT
    assert execution.result.text is None
    assert execution.output_bytes == 2


def test_real_observed_pdf_worker_retains_actual_guard_or_page_response_size() -> None:
    # Arrange
    pages = ("Independent copper telescope fact.",)
    source = build_text_pdf(pages)
    source_hash = sha256(source).hexdigest()
    offline = externally_offline()
    expected_payload = json.dumps(
        {
            "version": 2,
            "outcome": "success",
            "source_sha256": source_hash,
            "pages": [{"page_number": 1, "text": pages[0]}],
            "total_pages": 1,
            "missing_pages": [],
        },
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    # Act
    execution = run_observed_pdf_worker(source, max_pages=1)
    # Assert
    assert execution.result.source_sha256 == source_hash
    if offline:
        assert execution.result.outcome is PdfWorkerOutcome.SUCCESS
        assert execution.result.pages[0].text == pages[0]
        assert execution.output_bytes == len(expected_payload)
    else:
        assert execution.result.outcome is PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
        assert execution.result.pages == ()
        assert execution.output_bytes == 0


@pytest.mark.parametrize("kind", ["text", "pdf"])
def test_nonlinux_observed_entry_has_explicit_zero_consumption_without_launch(
    kind: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    module = importlib.import_module(
        "soulkiller_text.run_text_worker" if kind == "text" else "soulkiller_text.pdf_worker"
    )
    calls: list[object] = []
    monkeypatch.setattr(module.sys, "platform", "win32")
    monkeypatch.setattr(module, "run_command", lambda *args, **kwargs: calls.append(args))
    # Act
    execution = (
        run_observed_text_worker(BILINGUAL_BYTES)
        if kind == "text"
        else run_observed_pdf_worker(BILINGUAL_BYTES)
    )
    # Assert
    assert execution.result.outcome == "unsupported_environment"
    assert execution.output_bytes == 0
    assert calls == []


@pytest.mark.parametrize("capability", ["waitid", "WNOWAIT"])
def test_missing_exit_guard_returns_zero_consumption_before_candidate_launch(
    capability: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    calls: list[object] = []
    monkeypatch.delattr(os, capability)
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: calls.append(args))
    # Act
    execution = run_observed_text_worker(BILINGUAL_BYTES)
    # Assert
    assert execution.result.outcome is WorkerOutcome.UNSUPPORTED_ENVIRONMENT
    assert execution.output_bytes == 0
    assert calls == []


@pytest.mark.parametrize("failure", [KeyboardInterrupt, RuntimeError])
def test_observation_interruption_propagates_only_after_worker_cleanup(
    failure: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    processes = record_processes(monkeypatch)
    counter = WorkerOutputCounter()

    def interrupted(byte_count: int) -> None:
        counter.observe(byte_count)
        raise failure("synthetic interruption")

    command = responding_command(result_payload(BILINGUAL_SHA256))
    # Act
    with pytest.raises(failure, match="synthetic interruption"):
        run_command(command, BILINGUAL_BYTES, WorkerLimits(), output_observer=interrupted)
    # Assert
    assert counter.output_bytes > 0
    assert_reaped(processes)


@pytest.mark.parametrize("kind", ["text", "pdf"])
@pytest.mark.parametrize("failure", [KeyboardInterrupt, WorkerCleanupError])
def test_observed_fixed_entry_does_not_return_completed_record_after_exception(
    kind: str, failure: type[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    module = importlib.import_module(
        "soulkiller_text.run_text_worker" if kind == "text" else "soulkiller_text.pdf_worker"
    )
    error = failure()
    calls: list[object] = []

    def interrupted(*args: object, **kwargs: object) -> None:
        calls.append(args)
        raise error

    monkeypatch.setattr(module, "run_command", interrupted)
    # Act
    with pytest.raises(failure) as raised:
        if kind == "text":
            run_observed_text_worker(BILINGUAL_BYTES)
        else:
            run_observed_pdf_worker(BILINGUAL_BYTES)
    # Assert
    assert raised.value is error
    assert len(calls) == 1


def test_execution_record_is_frozen_without_replacing_existing_worker_result() -> None:
    # Arrange
    result = WorkerResult(WorkerOutcome.SUCCESS, BILINGUAL_SHA256, BILINGUAL_TEXT)
    execution = WorkerExecution(result, 193)
    # Act
    with pytest.raises(FrozenInstanceError):
        execution.output_bytes = 0  # type: ignore[misc]
    # Assert
    assert execution.result is result
    assert execution.output_bytes == 193
