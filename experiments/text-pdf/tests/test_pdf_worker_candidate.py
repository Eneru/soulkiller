"""The PDF candidate emits only bounded byte-derived protocol evidence."""

import io
import json
import sys

import pytest

from soulkiller_text import pdf_worker_candidate
from soulkiller_text.pdf_outcome import PdfOutcome
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_result import PdfResult

from .pdf_worker_fixtures import PDF_TEXT, pdf_record
from .synthetic_sources import BILINGUAL_BYTES, BILINGUAL_SHA256


def test_candidate_reads_bounded_bytes_and_emits_expected_page_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    input_buffer, output_buffer = io.BytesIO(BILINGUAL_BYTES), io.BytesIO()
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(input_buffer))
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(output_buffer))
    invocations: list[tuple[bytes, int]] = []

    def extract(source: bytes, max_pages: int) -> PdfResult:
        invocations.append((source, max_pages))
        return PdfResult(PdfOutcome.SUCCESS, BILINGUAL_SHA256, (PdfPage(1, PDF_TEXT),), 1, ())

    monkeypatch.setattr(pdf_worker_candidate, "extract_native_pdf", extract)
    # Act
    code = pdf_worker_candidate.run_candidate(2)
    # Assert
    assert code == 0
    assert invocations == [(BILINGUAL_BYTES, 2)]
    assert input_buffer.tell() == len(BILINGUAL_BYTES)
    assert json.loads(output_buffer.getvalue()) == pdf_record()


def test_oversized_child_input_has_no_candidate_call_or_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Arrange
    cap = 5 * 1024**2
    input_buffer, output_buffer = io.BytesIO(b"x" * (cap + 2)), io.BytesIO()
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(input_buffer))
    monkeypatch.setattr(sys, "stdout", io.TextIOWrapper(output_buffer))
    invocations: list[object] = []
    monkeypatch.setattr(
        pdf_worker_candidate, "extract_native_pdf", lambda *args, **kwargs: invocations.append(args)
    )
    # Act
    code = pdf_worker_candidate.run_candidate(20)
    # Assert
    assert code == 2
    assert input_buffer.tell() == cap + 1
    assert output_buffer.getvalue() == b""
    assert invocations == []
