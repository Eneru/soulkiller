"""Worker page evidence is immutable and uses an explicit outcome enum."""

from dataclasses import FrozenInstanceError

import pytest

from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult

from .pdf_worker_fixtures import PDF_TEXT
from .synthetic_sources import BILINGUAL_SHA256


@pytest.mark.parametrize(
    "field", ["outcome", "source_sha256", "pages", "total_pages", "missing_pages"]
)
def test_pdf_worker_result_fields_are_frozen(field: str) -> None:
    # Arrange
    result = PdfWorkerResult(
        PdfWorkerOutcome.SUCCESS, BILINGUAL_SHA256, (PdfPage(1, PDF_TEXT),), 1, ()
    )
    # Act / Assert
    with pytest.raises(FrozenInstanceError):
        setattr(result, field, None)


def test_pdf_worker_outcome_exposes_adapter_and_supervisor_classifications() -> None:
    # Arrange
    expected = {
        "success",
        "no_text",
        "encrypted_pdf",
        "malformed_input",
        "page_limit",
        "partial",
        "unsupported_dependency",
        "candidate_failure",
        "timeout",
        "resource_limit",
        "output_limit",
        "protocol_error",
        "unsupported_environment",
    }
    # Act
    actual = {outcome.value for outcome in PdfWorkerOutcome}
    # Assert
    assert actual == expected
