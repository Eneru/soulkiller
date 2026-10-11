"""Classify PDF completion from observed process guards and verified evidence."""

from .pdf_constants import MAX_PDF_PAGES
from .pdf_wire_protocol import decode_result
from .pdf_worker_outcome import PdfWorkerOutcome
from .pdf_worker_result import PdfWorkerResult
from .worker_constants import MEMORY_FAILURE_EXIT, SUCCESS_EXIT, UNSUPPORTED_EXIT
from .worker_outcome import WorkerOutcome


def classify_completion(
    return_code: int | None,
    pipe_failure: WorkerOutcome | None,
    response: bytes,
    source_sha256: str,
    max_pages: int = MAX_PDF_PAGES,
) -> PdfWorkerResult:
    """Cap/deadline failures override responses; rejected evidence never escapes."""
    if pipe_failure in (WorkerOutcome.TIMEOUT, WorkerOutcome.OUTPUT_LIMIT):
        outcome = PdfWorkerOutcome(pipe_failure.value)
    elif return_code is None:
        outcome = PdfWorkerOutcome.TIMEOUT
    elif return_code == UNSUPPORTED_EXIT:
        outcome = PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT
    elif return_code == MEMORY_FAILURE_EXIT:
        outcome = PdfWorkerOutcome.RESOURCE_LIMIT
    elif return_code != SUCCESS_EXIT or pipe_failure == WorkerOutcome.CANDIDATE_FAILURE:
        outcome = PdfWorkerOutcome.CANDIDATE_FAILURE
    else:
        try:
            return decode_result(response, source_sha256, max_pages)
        except ValueError:
            outcome = PdfWorkerOutcome.PROTOCOL_ERROR
    return PdfWorkerResult(outcome, source_sha256, (), None, ())
