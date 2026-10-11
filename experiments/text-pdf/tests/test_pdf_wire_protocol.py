"""Strict independently authored page records never promote unverified evidence."""

import json

import pytest

from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_wire_protocol import decode_result, encode_result
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult

from .pdf_worker_fixtures import PDF_TEXT, pdf_payload, pdf_record
from .synthetic_sources import BILINGUAL_SHA256


def test_encoder_emits_exact_versioned_ascii_page_record() -> None:
    # Arrange
    result = PdfWorkerResult(
        PdfWorkerOutcome.SUCCESS, BILINGUAL_SHA256, (PdfPage(1, PDF_TEXT),), 1, ()
    )
    # Act
    payload = encode_result(result)
    # Assert
    assert payload.isascii()
    assert json.loads(payload) == pdf_record()


def test_decoder_preserves_hash_unicode_and_physical_page() -> None:
    # Arrange
    payload = pdf_payload()
    # Act
    result = decode_result(payload, BILINGUAL_SHA256)
    # Assert
    assert result == PdfWorkerResult(
        PdfWorkerOutcome.SUCCESS, BILINGUAL_SHA256, (PdfPage(1, PDF_TEXT),), 1, ()
    )
    assert result.outcome is PdfWorkerOutcome.SUCCESS


@pytest.mark.parametrize(
    ("outcome", "pages", "total", "missing"),
    [
        ("no_text", [{"page_number": 1, "text": "  \n"}], 1, []),
        ("no_text", [], 0, []),
        ("partial", [{"page_number": 2, "text": "Invented fact."}], 3, [1, 3]),
        ("encrypted_pdf", [], None, []),
        ("malformed_input", [], None, []),
        ("unsupported_dependency", [], 2, [1, 2]),
        ("candidate_failure", [], 1, [1]),
        ("page_limit", [], 21, []),
    ],
)
def test_supported_outcomes_preserve_explicit_coverage(
    outcome: str, pages: list[dict[str, object]], total: int | None, missing: list[int]
) -> None:
    # Arrange
    record = pdf_record(outcome, pages=pages, total_pages=total, missing_pages=missing)
    # Act
    result = decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)
    # Assert
    assert result.outcome == outcome
    assert result.total_pages == total
    assert result.missing_pages == tuple(missing)
    assert tuple(page.page_number for page in result.pages) == tuple(
        page["page_number"] for page in pages
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", True),
        ("version", 1),
        ("version", 2.0),
        ("source_sha256", "0" * 64),
        ("source_sha256", BILINGUAL_SHA256.upper()),
        ("source_sha256", None),
        ("outcome", None),
        ("outcome", "invalid_encoding"),
        ("outcome", "timeout"),
        ("outcome", "resource_limit"),
        ("outcome", "output_limit"),
        ("outcome", "unsupported_environment"),
        ("outcome", "protocol_error"),
        ("pages", None),
        ("pages", {}),
        ("pages", "not pages"),
        ("total_pages", True),
        ("total_pages", 1.0),
        ("total_pages", -1),
        ("total_pages", None),
        ("total_pages", 0),
        ("total_pages", 21),
        ("missing_pages", None),
        ("missing_pages", {}),
        ("missing_pages", [True]),
        ("missing_pages", [1.0]),
        ("missing_pages", [0]),
        ("missing_pages", [2]),
    ],
)
def test_invalid_response_fields_are_rejected(field: str, value: object) -> None:
    # Arrange
    record = pdf_record()
    record[field] = value
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


@pytest.mark.parametrize(
    "pages",
    [
        [None],
        [{}],
        [{"page_number": 1}],
        [{"page_number": 1, "text": None}],
        [{"page_number": True, "text": PDF_TEXT}],
        [{"page_number": 1.0, "text": PDF_TEXT}],
        [{"page_number": 0, "text": PDF_TEXT}],
        [{"page_number": 2, "text": PDF_TEXT}],
        [{"page_number": 1, "text": "\ud800"}],
        [{"page_number": 1, "text": PDF_TEXT, "secret": "rejected"}],
        [{"page_number": 1, "text": ""}],
        [{"page_number": 1, "text": "   "}],
        [{"page_number": 1, "text": PDF_TEXT}] * 2,
    ],
)
def test_invalid_page_records_are_rejected(pages: list[object]) -> None:
    # Arrange
    record = pdf_record(pages=pages)
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


@pytest.mark.parametrize(
    "field", ["version", "outcome", "source_sha256", "pages", "total_pages", "missing_pages"]
)
def test_missing_required_field_is_rejected(field: str) -> None:
    # Arrange
    record = pdf_record()
    del record[field]
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


def test_unknown_root_field_is_rejected() -> None:
    # Arrange
    record = pdf_record()
    record["traceback"] = "private synthetic diagnostic"
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


@pytest.mark.parametrize(
    ("outcome", "pages", "total", "missing"),
    [
        ("success", [{"page_number": 1, "text": PDF_TEXT}], 2, [2]),
        ("no_text", [{"page_number": 1, "text": PDF_TEXT}], 1, []),
        ("partial", [{"page_number": 1, "text": PDF_TEXT}], 1, []),
        ("partial", [], 1, [1]),
        ("partial", [{"page_number": 1, "text": PDF_TEXT}], 2, [1, 2]),
        ("partial", [{"page_number": 1, "text": PDF_TEXT}], 3, [2, 2]),
        ("partial", [{"page_number": 1, "text": PDF_TEXT}], 3, [3, 2]),
        (
            "partial",
            [{"page_number": 3, "text": PDF_TEXT}, {"page_number": 1, "text": PDF_TEXT}],
            3,
            [2],
        ),
        ("partial", [{"page_number": 1, "text": PDF_TEXT}], 3, [2]),
        ("encrypted_pdf", [], 0, []),
        ("malformed_input", [{"page_number": 1, "text": PDF_TEXT}], 1, []),
        ("candidate_failure", [], 2, [1]),
        ("unsupported_dependency", [], None, [1]),
        ("page_limit", [], 20, []),
        ("page_limit", [{"page_number": 1, "text": PDF_TEXT}], 21, []),
        ("page_limit", [], 21, [1]),
    ],
)
def test_outcome_and_page_partition_inconsistencies_are_rejected(
    outcome: str, pages: list[dict[str, object]], total: int | None, missing: list[int]
) -> None:
    # Arrange
    record = pdf_record(outcome, pages=pages, total_pages=total, missing_pages=missing)
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(json.dumps(record).encode("ascii"), BILINGUAL_SHA256)


@pytest.mark.parametrize(
    "payload",
    [
        b"",
        b"not json",
        b"[]",
        b"null",
        b"true",
        b"1",
        b"{}",
        b"\xff",
        b'{"version":2,"version":2}',
        b'{"version":NaN}',
        b'{"version":Infinity}',
        b'{"version":-Infinity}',
        b"[" * 2000,
        pdf_payload() * 2,
    ],
)
def test_malformed_duplicate_nonfinite_or_repeated_response_is_rejected(payload: bytes) -> None:
    # Arrange
    response = payload
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(response, BILINGUAL_SHA256)


def test_nested_duplicate_page_field_is_rejected() -> None:
    # Arrange
    payload = pdf_payload().replace(b'"page_number": 1', b'"page_number": 1, "page_number": 1')
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(payload, BILINGUAL_SHA256)


@pytest.mark.parametrize("max_pages", [True, 0, 21, 1.0, None])
def test_invalid_decoder_page_budget_is_rejected(max_pages: object) -> None:
    # Arrange
    from typing import cast

    payload = pdf_payload()
    # Act / Assert
    with pytest.raises(ValueError):
        decode_result(payload, BILINGUAL_SHA256, cast(int, max_pages))


def test_small_budget_enforces_page_limit_without_allocating_declared_missing_pages() -> None:
    # Arrange
    payload = pdf_payload(outcome="page_limit", pages=[], total_pages=2**60)
    # Act
    result = decode_result(payload, BILINGUAL_SHA256, max_pages=1)
    # Assert
    assert result.outcome is PdfWorkerOutcome.PAGE_LIMIT
    assert result.total_pages == 2**60
    assert result.pages == ()
    assert result.missing_pages == ()
