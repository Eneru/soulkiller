"""Typed observations are validated before deterministic bounded encoding."""

import json
from collections.abc import Callable
from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import pytest

from soulkiller_text.fixture_record import encode_fixture_record
from soulkiller_text.fixture_record_error import FixtureRecordError
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.run_status import RunStatus
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .fixture_record_fixtures import (
    PAYLOAD_BYTES,
    PROBE_BYTES,
    exact_payload_document,
    failed_pdf_row,
    failed_text_row,
    pdf_document,
    pdf_row,
    text_document,
    text_row,
    wire,
)


@pytest.mark.parametrize(
    ("builder", "document"), [(text_row, text_document), (pdf_row, pdf_document)]
)
def test_encoder_matches_independent_literal_json(
    builder: Callable[[], FixtureRun],
    document: Callable[[], dict[str, object]],
) -> None:
    """Exact public JSON preserves text and excludes unrequested source metadata."""
    # Arrange
    row = builder()
    expected = document()
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)
    assert payload.isascii()
    assert "never-opened" not in payload.decode("ascii")
    assert "author_label" not in json.loads(payload)


@pytest.mark.parametrize(
    "outcome", [value for value in WorkerOutcome if value != WorkerOutcome.SUCCESS]
)
def test_encoder_retains_all_completed_text_failure_outcomes(outcome: WorkerOutcome) -> None:
    """Parent observations may retain supervisor failures that child messages cannot claim."""
    # Arrange
    row = failed_text_row(outcome)
    expected = text_document()
    expected["result"] = {"outcome": outcome.value, "text": None}
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)


@pytest.mark.parametrize(
    "outcome",
    [
        PdfWorkerOutcome.ENCRYPTED_PDF,
        PdfWorkerOutcome.MALFORMED_INPUT,
        PdfWorkerOutcome.UNSUPPORTED_DEPENDENCY,
        PdfWorkerOutcome.CANDIDATE_FAILURE,
        PdfWorkerOutcome.TIMEOUT,
        PdfWorkerOutcome.RESOURCE_LIMIT,
        PdfWorkerOutcome.OUTPUT_LIMIT,
        PdfWorkerOutcome.PROTOCOL_ERROR,
        PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT,
    ],
)
def test_encoder_retains_empty_completed_pdf_failures(outcome: PdfWorkerOutcome) -> None:
    """Unavailable PDF evidence stays empty rather than becoming an invented page."""
    # Arrange
    row = failed_pdf_row(outcome)
    expected = pdf_document()
    expected["result"] = {
        "outcome": outcome.value,
        "pages": [],
        "total_pages": None,
        "missing_pages": [],
    }
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)


@pytest.mark.parametrize("count", [0, PROBE_BYTES])
def test_encoder_accepts_observed_zero_and_single_overflow_probe(count: int) -> None:
    """Observed transport consumption includes the supervisor's one-byte overflow probe."""
    # Arrange
    row = replace(text_row(), output_bytes=count)
    expected = text_document()
    expected["output_bytes"] = count
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)


@pytest.mark.parametrize("reason", [status for status in RunStatus if status != RunStatus.COMPLETE])
def test_encoder_keeps_never_started_zero_for_each_stop_reason(reason: RunStatus) -> None:
    """A never-started fixture has no result and a known zero count."""
    # Arrange
    row = replace(text_row(), result=None, output_bytes=0, unfinished_reason=reason)
    expected = text_document()
    expected.update(result=None, output_bytes=0, unfinished_reason=reason.value)
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)


@pytest.mark.parametrize("reason", [RunStatus.CANCELLED, RunStatus.CLEANUP_FAILURE])
def test_encoder_keeps_interrupted_output_unavailable(reason: RunStatus) -> None:
    """Null records an unknown active-call count rather than a fabricated zero."""
    # Arrange
    row = replace(text_row(), result=None, output_bytes=None, unfinished_reason=reason)
    expected = text_document()
    expected.update(result=None, output_bytes=None, unfinished_reason=reason.value)
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert payload == wire(expected)


@pytest.mark.parametrize("value", [None, object(), {}, "private synthetic diagnostic"])
def test_encoder_rejects_nonrow_objects_with_safe_error(value: object) -> None:
    """Only an exact typed row crosses the object trust boundary."""
    # Arrange
    supplied = cast(FixtureRun, value)
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        encode_fixture_record(supplied)
    # Assert
    assert failure.value.category == "invalid_fixture_record"
    assert str(failure.value) == "invalid_fixture_record"


@pytest.mark.parametrize("count", [None, True, False, -1, 1.0, "1", PROBE_BYTES + 1])
def test_encoder_rejects_invalid_completed_counts(count: object) -> None:
    """Known counts are exact integers within the reviewed transport bound."""
    # Arrange
    row = replace(text_row(), output_bytes=cast(int, count))
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        encode_fixture_record(row)
    # Assert
    assert failure.value.category == "invalid_fixture_record"


@pytest.mark.parametrize("reason", [RunStatus.COMPLETE, RunStatus.CANCELLED, "cancelled"])
def test_encoder_rejects_unfinished_reason_on_completed_result(reason: object) -> None:
    """A returned worker result cannot simultaneously claim an unfinished call."""
    # Arrange
    row = replace(text_row(), unfinished_reason=cast(RunStatus, reason))
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(row)


@pytest.mark.parametrize(
    ("reason", "count"),
    [
        (None, 0),
        (RunStatus.COMPLETE, 0),
        (RunStatus.TIME_LIMIT, None),
        (RunStatus.OUTPUT_LIMIT, None),
        (RunStatus.UNSUPPORTED_ENVIRONMENT, None),
        (RunStatus.CANCELLED, 1),
        (RunStatus.CLEANUP_FAILURE, 1),
        (RunStatus.CANCELLED, True),
        ("cancelled", None),
    ],
)
def test_encoder_rejects_inconsistent_unfinished_observations(
    reason: object, count: object
) -> None:
    """Unfinished rows permit only documented stop reasons and zero or unknown counts."""
    # Arrange
    row = replace(
        text_row(),
        result=None,
        output_bytes=cast(int, count),
        unfinished_reason=cast(RunStatus, reason),
    )
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(row)


@pytest.mark.parametrize("text", [None, "", 12, True, "\ud800"])
def test_encoder_rejects_invalid_success_text(text: object) -> None:
    """Successful TXT evidence is nonempty scalar Unicode without coercion."""
    # Arrange
    row = text_row()
    result = WorkerResult(WorkerOutcome.SUCCESS, row.specification.sha256, cast(str, text))
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))


def test_encoder_rejects_text_attached_to_failed_outcome() -> None:
    """Failed TXT calls cannot smuggle partial evidence into a persisted result."""
    # Arrange
    row = text_row()
    result = WorkerResult(WorkerOutcome.TIMEOUT, row.specification.sha256, "unverified text")
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))


@pytest.mark.parametrize("kind", ["txt-as-pdf", "pdf-as-txt", "wrong-hash", "string-enum"])
def test_encoder_rejects_forged_result_identity_or_type(kind: str) -> None:
    """Permissive value containers do not establish format, revision or enum validity."""
    # Arrange
    row = text_row()
    if kind == "txt-as-pdf":
        row = replace(pdf_row(), result=text_row().result)
    elif kind == "pdf-as-txt":
        row = replace(row, result=pdf_row().result)
    elif kind == "wrong-hash":
        row = replace(row, result=WorkerResult(WorkerOutcome.SUCCESS, "a" * 64, "invented"))
    else:
        row = replace(
            row,
            result=WorkerResult(
                cast(WorkerOutcome, "success"), row.specification.sha256, "invented"
            ),
        )
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(row)


@pytest.mark.parametrize(
    "outcome",
    [
        PdfWorkerOutcome.TIMEOUT,
        PdfWorkerOutcome.RESOURCE_LIMIT,
        PdfWorkerOutcome.OUTPUT_LIMIT,
        PdfWorkerOutcome.PROTOCOL_ERROR,
        PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT,
    ],
)
def test_encoder_rejects_pdf_evidence_on_supervisor_only_failure(outcome: PdfWorkerOutcome) -> None:
    """A failed transport observation cannot retain candidate page evidence."""
    # Arrange
    row = pdf_row()
    result = PdfWorkerResult(outcome, row.specification.sha256, (PdfPage(1, "partial"),), 1, ())
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))


def test_encoder_accepts_exact_frame_adjusted_byte_ceiling() -> None:
    """The largest permitted JSON payload leaves room for the 48-byte storage frame."""
    # Arrange
    document = exact_payload_document()
    nested = cast(dict[str, object], document["result"])
    row = text_row()
    result = WorkerResult(
        WorkerOutcome.SUCCESS, row.specification.sha256, cast(str, nested["text"])
    )
    # Act
    payload = encode_fixture_record(replace(row, result=result))
    # Assert
    assert len(payload) == PAYLOAD_BYTES
    assert payload == wire(document)


@pytest.mark.parametrize("character", ["x", "é", "\U0001f31f"])
def test_encoder_refuses_json_expansion_one_byte_past_frame_budget(character: str) -> None:
    """ASCII escaping counts toward storage bytes; text is never silently truncated."""
    # Arrange
    document = exact_payload_document(1, character)
    nested = cast(dict[str, object], document["result"])
    row = text_row()
    result = WorkerResult(
        WorkerOutcome.SUCCESS, row.specification.sha256, cast(str, nested["text"])
    )
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        encode_fixture_record(replace(row, result=result))
    # Assert
    assert failure.value.category == "fixture_record_too_large"
    assert len(wire(document)) == PAYLOAD_BYTES + 1


def test_encoder_does_not_equate_expected_and_observed_outcomes() -> None:
    """An independent reference mismatch remains an observation rather than a codec error."""
    # Arrange
    row = failed_text_row(WorkerOutcome.INVALID_ENCODING)
    # Act
    payload = encode_fixture_record(row)
    # Assert
    assert json.loads(payload)["result"]["outcome"] == "invalid_encoding"
    assert row.specification.outcome == "success"


@pytest.mark.parametrize("kind", ["row", "specification", "result", "page"])
def test_encoder_rejects_missing_required_dataclass_attributes(kind: str) -> None:
    """Forged exact classes with missing fields fail through the fixed public error contract."""
    # Arrange
    row = pdf_row() if kind == "page" else text_row()
    if kind == "row":
        object.__delattr__(row, "specification")
    elif kind == "specification":
        object.__delattr__(row.specification, "sha256")
    elif kind == "result":
        assert row.result is not None
        object.__delattr__(row.result, "outcome")
    else:
        assert isinstance(row.result, PdfWorkerResult)
        object.__delattr__(row.result.pages[0], "text")
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        encode_fixture_record(row)
    # Assert
    assert failure.value.category == "invalid_fixture_record"
    assert str(failure.value) == "invalid_fixture_record"


@pytest.mark.parametrize(
    "kind", ["cross-enum", "list-pages", "list-missing", "wrong-page", "page-bool"]
)
def test_encoder_refuses_forged_pdf_enums_and_containers(kind: str) -> None:
    """Value equality and iterable shape cannot substitute for exact typed PDF objects."""
    # Arrange
    row = pdf_row()
    assert isinstance(row.result, PdfWorkerResult)
    result = row.result
    if kind == "cross-enum":
        result = replace(result, outcome=cast(PdfWorkerOutcome, WorkerOutcome.SUCCESS))
    elif kind == "list-pages":
        result = replace(result, pages=cast(tuple[PdfPage, ...], list(result.pages)))
    elif kind == "list-missing":
        result = replace(result, missing_pages=cast(tuple[int, ...], []))
    elif kind == "wrong-page":
        page = SimpleNamespace(page_number=1, text="Invented")
        result = replace(result, pages=(cast(PdfPage, page),))
    else:
        result = replace(result, pages=(PdfPage(True, "Invented"),))
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))


def test_encoder_rejects_wrong_enum_domain_despite_equal_text_value() -> None:
    """StrEnum members from the PDF domain must not become typed TXT outcomes."""
    # Arrange
    row = text_row()
    result = WorkerResult(
        cast(WorkerOutcome, PdfWorkerOutcome.SUCCESS), row.specification.sha256, "Invented"
    )
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))


@pytest.mark.parametrize("kind", ["overlap", "missing-coverage", "empty-success", "bad-total"])
def test_encoder_rejects_inconsistent_typed_pdf_partition(kind: str) -> None:
    """Typed PDF objects receive the same semantic coverage checks as JSON records."""
    # Arrange
    row = pdf_row()
    assert isinstance(row.result, PdfWorkerResult)
    result = row.result
    if kind == "overlap":
        result = replace(result, missing_pages=(1,))
    elif kind == "missing-coverage":
        result = replace(result, pages=(PdfPage(1, "Invented"),))
    elif kind == "empty-success":
        result = replace(result, pages=(PdfPage(1, ""), PdfPage(2, "  ")))
    else:
        result = replace(result, total_pages=True)
    # Act
    with pytest.raises(FixtureRecordError):
        encode_fixture_record(replace(row, result=result))
