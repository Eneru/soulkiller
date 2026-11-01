"""Literal JSON decoding rejects untrusted framing and inconsistent observations."""

from dataclasses import replace
from typing import cast

import pytest

from soulkiller_text.corpus_fixture import CorpusFixture
from soulkiller_text.fixture_record import decode_fixture_record
from soulkiller_text.fixture_record_error import FixtureRecordError
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
    pdf_document,
    pdf_row,
    pdf_specification,
    text_document,
    text_row,
    text_specification,
    wire,
)
from .synthetic_sources import BILINGUAL_TEXT


def test_literal_bilingual_text_decodes_without_source_access() -> None:
    """Absent source paths cannot prevent restoring exact verified observation values."""
    # Arrange
    specification = text_specification()
    payload = wire(text_document())
    # Act
    restored = decode_fixture_record(payload, specification)
    # Assert
    assert restored == text_row()
    assert restored.specification is specification
    assert restored.result is not None
    assert isinstance(restored.result, WorkerResult)
    assert restored.result.text == BILINGUAL_TEXT


def test_literal_pdf_decodes_blank_and_nonempty_physical_pages() -> None:
    """Literal pages keep their original order and preserve blank-page coverage."""
    # Arrange
    specification = pdf_specification()
    # Act
    restored = decode_fixture_record(wire(pdf_document()), specification)
    # Assert
    assert restored == pdf_row()
    assert restored.specification is specification


@pytest.mark.parametrize(
    "outcome", [value for value in WorkerOutcome if value != WorkerOutcome.SUCCESS]
)
def test_decoder_accepts_persisted_parent_text_failure(outcome: WorkerOutcome) -> None:
    """Storage represents both candidate and supervisor outcomes without changing child trust."""
    # Arrange
    document = text_document()
    document["result"] = {"outcome": outcome.value, "text": None}
    # Act
    restored = decode_fixture_record(wire(document), text_specification())
    # Assert
    assert restored.result is not None
    assert restored.result.outcome is outcome
    assert restored.output_bytes == 157 and restored.unfinished_reason is None


@pytest.mark.parametrize("reason", [status for status in RunStatus if status != RunStatus.COMPLETE])
def test_decoder_restores_each_never_started_stop_reason(reason: RunStatus) -> None:
    """The per-row record preserves schedule interruption without inventing a worker result."""
    # Arrange
    document = text_document()
    document.update(result=None, output_bytes=0, unfinished_reason=reason.value)
    # Act
    restored = decode_fixture_record(wire(document), text_specification())
    # Assert
    assert restored.result is None
    assert restored.output_bytes == 0
    assert restored.unfinished_reason is reason


@pytest.mark.parametrize("reason", [RunStatus.CANCELLED, RunStatus.CLEANUP_FAILURE])
def test_decoder_preserves_unknown_interrupted_transport_count(reason: RunStatus) -> None:
    """An unavailable byte count remains null when active work was interrupted."""
    # Arrange
    document = text_document()
    document.update(result=None, output_bytes=None, unfinished_reason=reason.value)
    # Act
    restored = decode_fixture_record(wire(document), text_specification())
    # Assert
    assert restored.output_bytes is None
    assert restored.unfinished_reason is reason


@pytest.mark.parametrize(
    ("outcome", "pages", "total", "missing"),
    [
        (
            "success",
            [{"page_number": 1, "text": "Invented"}, {"page_number": 2, "text": ""}],
            2,
            [],
        ),
        ("no_text", [{"page_number": 1, "text": ""}, {"page_number": 2, "text": "  "}], 2, []),
        ("no_text", [], 0, []),
        ("partial", [{"page_number": 2, "text": "Recovered"}], 2, [1]),
        ("page_limit", [], 3, []),
        ("candidate_failure", [], 2, [1, 2]),
    ],
)
def test_decoder_retains_valid_pdf_evidence_partitions(
    outcome: str,
    pages: list[dict[str, object]],
    total: int,
    missing: list[int],
) -> None:
    """Candidate outcomes retain complete, partial, zero-page or over-limit evidence explicitly."""
    # Arrange
    document = pdf_document()
    document["result"] = {
        "outcome": outcome,
        "pages": pages,
        "total_pages": total,
        "missing_pages": missing,
    }
    # Act
    restored = decode_fixture_record(wire(document), pdf_specification())
    # Assert
    assert restored.result is not None
    assert isinstance(restored.result, PdfWorkerResult)
    assert restored.result.outcome is PdfWorkerOutcome(outcome)
    assert restored.result.pages == tuple(
        PdfPage(cast(int, p["page_number"]), cast(str, p["text"])) for p in pages
    )
    assert restored.result.total_pages == total
    assert restored.result.missing_pages == tuple(missing)


@pytest.mark.parametrize(
    "outcome",
    [
        "encrypted_pdf",
        "malformed_input",
        "unsupported_dependency",
        "candidate_failure",
        "timeout",
        "resource_limit",
        "output_limit",
        "protocol_error",
        "unsupported_environment",
    ],
)
def test_decoder_restores_completed_pdf_failures_with_unknown_page_count(outcome: str) -> None:
    """Unobserved page totals stay unavailable for failures of parsing or supervision."""
    # Arrange
    document = pdf_document()
    document["result"] = {
        "outcome": outcome,
        "pages": [],
        "total_pages": None,
        "missing_pages": [],
    }
    # Act
    restored = decode_fixture_record(wire(document), pdf_specification())
    # Assert
    assert restored.result is not None
    assert isinstance(restored.result, PdfWorkerResult)
    assert restored.result.outcome is PdfWorkerOutcome(outcome)
    assert restored.result.total_pages is None


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "fixture_id",
        "format",
        "source_sha256",
        "result",
        "output_bytes",
        "unfinished_reason",
    ],
)
def test_decoder_rejects_each_missing_envelope_field(field: str) -> None:
    """No required envelope field is supplied through an implicit default."""
    # Arrange
    document = text_document()
    del document[field]
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), text_specification())


def test_decoder_rejects_unknown_envelope_field() -> None:
    """Unknown envelope data cannot silently become an unversioned extension."""
    # Arrange
    document = text_document()
    document["private_diagnostic"] = "not for disclosure"
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        decode_fixture_record(wire(document), text_specification())
    # Assert
    assert str(failure.value) == "invalid_fixture_record"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("schema_version", 1.0),
        ("schema_version", "1"),
        ("schema_version", 0),
        ("schema_version", 2),
        ("schema_version", None),
        ("fixture_id", "other-id"),
        ("fixture_id", None),
        ("fixture_id", 1),
        ("format", "pdf"),
        ("format", "TXT"),
        ("format", None),
        ("source_sha256", "a" * 64),
        ("source_sha256", "A" * 64),
        ("source_sha256", None),
        ("output_bytes", True),
        ("output_bytes", 1.0),
        ("output_bytes", -1),
        ("output_bytes", PROBE_BYTES + 1),
        ("output_bytes", None),
        ("output_bytes", "157"),
        ("unfinished_reason", "complete"),
        ("unfinished_reason", "unknown"),
        ("unfinished_reason", True),
    ],
)
def test_decoder_rejects_invalid_scalar_or_binding(field: str, value: object) -> None:
    """Version, identity, revision and completed counts are checked without coercion."""
    # Arrange
    document = text_document()
    document[field] = value
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), text_specification())


@pytest.mark.parametrize("count", [0, PROBE_BYTES])
def test_decoder_accepts_known_observed_count_endpoints(count: int) -> None:
    """Known zero and the bounded overflow probe are distinct valid observations."""
    # Arrange
    document = text_document()
    document["output_bytes"] = count
    # Act
    restored = decode_fixture_record(wire(document), text_specification())
    # Assert
    assert restored.output_bytes == count


@pytest.mark.parametrize(
    "nested",
    [
        None,
        [],
        1,
        {"outcome": "success"},
        {"text": "invented"},
        {"outcome": "success", "text": "invented", "extra": True},
        {"outcome": "unknown", "text": None},
        {"outcome": True, "text": None},
        {"outcome": "success", "text": ""},
        {"outcome": "success", "text": None},
        {"outcome": "success", "text": True},
        {"outcome": "success", "text": "\udfff"},
        {"outcome": "timeout", "text": "unverified"},
    ],
)
def test_decoder_rejects_invalid_nested_text_record(nested: object) -> None:
    """TXT result records enforce exact fields and outcome-specific scalar evidence."""
    # Arrange
    document = text_document()
    document["result"] = nested
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), text_specification())


@pytest.mark.parametrize(
    ("reason", "count"),
    [
        (None, 0),
        ("complete", 0),
        ("time_limit", None),
        ("output_limit", None),
        ("unsupported_environment", None),
        ("cancelled", 1),
        ("cleanup_failure", 1),
        ("cancelled", True),
        ("unknown", 0),
    ],
)
def test_decoder_rejects_invalid_unfinished_observation(reason: object, count: object) -> None:
    """Null result rows cannot claim completed status, positive or unsupported unknown counts."""
    # Arrange
    document = text_document()
    document.update(result=None, output_bytes=count, unfinished_reason=reason)
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), text_specification())


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"null",
        b"[]",
        b"42",
        b"true",
        b"{}",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{} trailing",
        b'{"output_bytes":NaN}',
        b'{"output_bytes":Infinity}',
        b"[" * 2000 + b"0" + b"]" * 2000,
    ],
)
def test_decoder_rejects_malformed_or_nonobject_json(payload: bytes) -> None:
    """Invalid UTF-8, nonfinite constants, trailing and recursive JSON produce one safe error."""
    # Arrange
    specification = text_specification()
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        decode_fixture_record(payload, specification)
    # Assert
    assert failure.value.category == "invalid_fixture_record"


@pytest.mark.parametrize("kind", ["envelope", "result", "page"])
def test_decoder_rejects_duplicate_json_keys_at_each_nesting(kind: str) -> None:
    """Duplicate fields are invalid even when the repeated value is identical."""
    # Arrange
    document = pdf_document() if kind == "page" else text_document()
    payload = wire(document)
    token = {
        "envelope": b'"schema_version":1',
        "result": b'"outcome":"success"',
        "page": b'"page_number":1',
    }[kind]
    payload = payload.replace(token, token + b"," + token, 1)
    specification = pdf_specification() if kind == "page" else text_specification()
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(payload, specification)


@pytest.mark.parametrize("payload", [None, "{}", bytearray(b"{}"), memoryview(b"{}")])
def test_decoder_rejects_nonbytes_payload(payload: object) -> None:
    """The byte boundary does not implicitly copy or coerce unrelated input objects."""
    # Arrange
    specification = text_specification()
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(cast(bytes, payload), specification)


@pytest.mark.parametrize("field", ["outcome", "pages", "total_pages", "missing_pages"])
def test_decoder_rejects_missing_pdf_result_field(field: str) -> None:
    """Persisted PDF evidence always declares its complete nested shape."""
    # Arrange
    document = pdf_document()
    result = cast(dict[str, object], document["result"])
    del result[field]
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), pdf_specification())


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("unknown", 1),
        ("outcome", "unknown"),
        ("pages", None),
        ("pages", {}),
        ("total_pages", True),
        ("total_pages", -1),
        ("total_pages", 2.0),
        ("total_pages", 1),
        ("total_pages", 3),
        ("missing_pages", [1]),
        ("missing_pages", [True]),
        ("missing_pages", [2, 1]),
        ("missing_pages", [1, 1]),
        ("pages", [{"page_number": True, "text": "invented"}]),
        ("pages", [{"page_number": 0, "text": "invented"}]),
        ("pages", [{"page_number": 3, "text": "invented"}]),
        ("pages", [{"page_number": 1, "text": "\ud800"}]),
        ("pages", [{"page_number": 1, "text": "invented", "extra": 1}]),
        ("pages", [{"page_number": 2, "text": "two"}, {"page_number": 1, "text": "one"}]),
    ],
)
def test_decoder_rejects_malformed_or_inconsistent_pdf_evidence(field: str, value: object) -> None:
    """Physical-page numbering and the covered/missing partition remain independently validated."""
    # Arrange
    document = pdf_document()
    result = cast(dict[str, object], document["result"])
    result[field] = value
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), pdf_specification())


@pytest.mark.parametrize(
    "outcome",
    [
        "timeout",
        "resource_limit",
        "output_limit",
        "protocol_error",
        "unsupported_environment",
    ],
)
def test_decoder_rejects_supervisor_failure_with_candidate_evidence(outcome: str) -> None:
    """Observed supervisor failures cannot carry a completed or partial candidate page partition."""
    # Arrange
    document = pdf_document()
    result = cast(dict[str, object], document["result"])
    result["outcome"] = outcome
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(document), pdf_specification())


@pytest.mark.parametrize("page_count", [True, 0, 21, 2.0, None])
def test_decoder_rejects_invalid_supplied_pdf_ceiling(page_count: object) -> None:
    """Caller metadata still needs an exact bounded declared page ceiling."""
    # Arrange
    specification = replace(pdf_specification(), page_count=cast(int, page_count))
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(pdf_document()), specification)


def test_decoder_rejects_pdf_record_above_supplied_declared_page_cap() -> None:
    """A valid record for two pages is not accepted under a one-page caller specification."""
    # Arrange
    specification = replace(pdf_specification(), page_count=1)
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(pdf_document()), specification)


@pytest.mark.parametrize("field", ["fixture_id", "sha256", "format"])
def test_decoder_rejects_malformed_supplied_text_identity(field: str) -> None:
    """Even accepted-source callers cannot pass forged identity fields unnoticed."""
    # Arrange
    specification = text_specification()
    if field == "fixture_id":
        specification = replace(specification, fixture_id="bad/id")
    elif field == "sha256":
        specification = replace(specification, sha256="A" * 64)
    else:
        specification = replace(specification, format=cast(object, "pdf"))  # type: ignore[arg-type]
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(wire(text_document()), specification)


def test_decoder_accepts_exact_frame_adjusted_payload_size() -> None:
    """The byte ceiling accepts a complete largest-size record without truncating evidence."""
    # Arrange
    document = exact_payload_document()
    payload = wire(document)
    # Act
    restored = decode_fixture_record(payload, text_specification())
    # Assert
    assert len(payload) == PAYLOAD_BYTES
    assert restored.result is not None
    assert isinstance(restored.result, WorkerResult)
    assert restored.result.text == cast(dict[str, object], document["result"])["text"]


def test_decoder_refuses_one_byte_above_payload_ceiling() -> None:
    """An oversized payload is rejected before it can be returned as a typed observation."""
    # Arrange
    payload = wire(exact_payload_document(1))
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        decode_fixture_record(payload, text_specification())
    # Assert
    assert failure.value.category == "fixture_record_too_large"


@pytest.mark.parametrize("field", ["fixture_id", "sha256", "format"])
def test_decoder_rejects_supplied_specification_with_missing_required_attribute(field: str) -> None:
    """A malformed exact dataclass fails safely without exposing attribute diagnostics."""
    # Arrange
    specification = text_specification()
    object.__delattr__(specification, field)
    # Act
    with pytest.raises(FixtureRecordError) as failure:
        decode_fixture_record(wire(text_document()), specification)
    # Assert
    assert failure.value.category == "invalid_fixture_record"
    assert str(failure.value) == "invalid_fixture_record"


@pytest.mark.parametrize("specification", [None, {}, object(), "private synthetic path"])
def test_decoder_refuses_objects_other_than_exact_fixture_classes(specification: object) -> None:
    """An arbitrary metadata-shaped object is not accepted as a caller specification."""
    # Arrange
    payload = wire(text_document())
    # Act
    with pytest.raises(FixtureRecordError):
        decode_fixture_record(payload, cast(CorpusFixture, specification))


def test_decoder_keeps_observation_when_reference_outcome_differs() -> None:
    """Reference declarations are not rewritten into observed extraction success."""
    # Arrange
    specification = replace(text_specification(), outcome="no_text")
    # Act
    restored = decode_fixture_record(wire(text_document()), specification)
    # Assert
    assert restored.result is not None
    assert restored.result.outcome is WorkerOutcome.SUCCESS
    assert restored.specification.outcome == "no_text"
