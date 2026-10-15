"""Nested TXT/PDF row conversion without broadening trusted child-response protocols."""

from . import fixture_record_constants as constants
from .corpus_fixture import CorpusFixture
from .fixture_record_error import FixtureRecordError
from .fixture_record_fields import exact_fields, scalar_text
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_page import PdfPage
from .pdf_response_evidence import decode_count, decode_missing, decode_pages, validate_evidence
from .pdf_worker_outcome import PdfWorkerOutcome
from .pdf_worker_result import PdfWorkerResult
from .worker_outcome import WorkerOutcome
from .worker_result import WorkerResult

_SUPERVISOR_PDF_OUTCOMES = frozenset(
    {
        PdfWorkerOutcome.TIMEOUT,
        PdfWorkerOutcome.RESOURCE_LIMIT,
        PdfWorkerOutcome.OUTPUT_LIMIT,
        PdfWorkerOutcome.PROTOCOL_ERROR,
        PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT,
    }
)


def _pdf_fields(result: PdfWorkerResult, maximum: int) -> dict[str, object]:
    """Validate exact immutable page containers before serializing their declared values."""
    if (
        type(result.outcome) is not PdfWorkerOutcome
        or type(result.pages) is not tuple
        or type(result.missing_pages) is not tuple
        or len(result.pages) > maximum
        or len(result.missing_pages) > maximum
    ):
        raise FixtureRecordError(constants.INVALID_RECORD)
    pages: list[object] = []
    for page in result.pages:
        if type(page) is not PdfPage or type(page.page_number) is not int:
            raise FixtureRecordError(constants.INVALID_RECORD)
        pages.append({"page_number": page.page_number, "text": scalar_text(page.text)})
    return {
        "outcome": result.outcome.value,
        "pages": pages,
        "total_pages": result.total_pages,
        "missing_pages": list(result.missing_pages),
    }


def result_fields(
    result: WorkerResult | PdfWorkerResult | None,
    specification: CorpusFixture | PdfCorpusFixture,
) -> dict[str, object] | None:
    """Reject forged result types/revisions before converting the matching worker observation."""
    if result is None:
        return None
    if isinstance(specification, PdfCorpusFixture):
        if type(result) is not PdfWorkerResult:
            raise FixtureRecordError(constants.INVALID_RECORD)
        fields = _pdf_fields(result, specification.page_count)
    else:
        if type(result) is not WorkerResult or type(result.outcome) is not WorkerOutcome:
            raise FixtureRecordError(constants.INVALID_RECORD)
        fields = {"outcome": result.outcome.value, "text": result.text}
    if type(result.source_sha256) is not str or result.source_sha256 != specification.sha256:
        raise FixtureRecordError(constants.INVALID_RECORD)
    return fields


def _decode_text(value: object, source_sha256: str) -> WorkerResult:
    """Accept supervisor outcomes but preserve text only for nonempty successful TXT decoding."""
    fields = exact_fields(value, constants.TXT_RESULT_FIELDS)
    try:
        outcome = WorkerOutcome(scalar_text(fields["outcome"]))
    except ValueError:
        raise FixtureRecordError(constants.INVALID_RECORD) from None
    text = fields["text"]
    if outcome is WorkerOutcome.SUCCESS:
        text = scalar_text(text, allow_empty=False)
    elif text is not None:
        raise FixtureRecordError(constants.INVALID_RECORD)
    return WorkerResult(outcome, source_sha256, text)


def _decode_pdf(value: object, specification: PdfCorpusFixture) -> PdfWorkerResult:
    """Reuse physical-page invariants while refusing evidence on supervisor-only failures."""
    fields = exact_fields(value, constants.PDF_RESULT_FIELDS)
    try:
        outcome = PdfWorkerOutcome(scalar_text(fields["outcome"]))
        pages = decode_pages(fields["pages"], specification.page_count)
        total = decode_count(fields["total_pages"])
        missing = decode_missing(fields["missing_pages"], specification.page_count)
        if outcome in _SUPERVISOR_PDF_OUTCOMES:
            if pages or total is not None or missing:
                raise ValueError(constants.INVALID_RECORD)
        else:
            validate_evidence(outcome, pages, total, missing, specification.page_count)
    except ValueError:
        raise FixtureRecordError(constants.INVALID_RECORD) from None
    return PdfWorkerResult(outcome, specification.sha256, pages, total, missing)


def decode_nested_result(
    value: object, specification: CorpusFixture | PdfCorpusFixture
) -> WorkerResult | PdfWorkerResult | None:
    """Restore only the declared worker type, retaining absent observations without source I/O."""
    if value is None:
        return None
    if isinstance(specification, PdfCorpusFixture):
        return _decode_pdf(value, specification)
    return _decode_text(value, specification.sha256)
