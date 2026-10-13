"""Fixed supervised native PDF worker for immutable synthetic source bytes."""

import sys
from collections.abc import Callable
from functools import partial
from hashlib import sha256
from pathlib import Path

from .pdf_constants import MAX_PDF_PAGES
from .pdf_worker_completion import classify_completion
from .pdf_worker_outcome import PdfWorkerOutcome
from .pdf_worker_result import PdfWorkerResult
from .supervise import run_command, validate_source
from .worker_execution import WorkerExecution
from .worker_limits import WorkerLimits
from .worker_output_counter import WorkerOutputCounter


def _run_pdf_worker(
    source: bytes,
    limits: WorkerLimits | None,
    max_pages: int,
    output_observer: Callable[[int], None] | None,
) -> PdfWorkerResult:
    """Verify the inherited offline boundary and run only the fixed guarded parser."""
    validate_source(source)
    limits = WorkerLimits() if limits is None else limits
    if type(limits) is not WorkerLimits:
        raise ValueError("invalid_worker_limits")
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PDF_PAGES:
        raise ValueError("invalid_pdf_page_limit")
    if sys.platform != "linux":
        return PdfWorkerResult(
            PdfWorkerOutcome.UNSUPPORTED_ENVIRONMENT, sha256(source).hexdigest(), (), None, ()
        )
    command = (
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).with_name("pdf_worker_bootstrap.py").absolute()),
        str(limits.address_space_bytes),
        str(max_pages),
    )
    classifier = partial(classify_completion, max_pages=max_pages)
    if output_observer is None:
        return run_command(command, source, limits, classifier)
    return run_command(command, source, limits, classifier, output_observer=output_observer)


def run_pdf_worker(
    source: bytes,
    limits: WorkerLimits | None = None,
    max_pages: int = MAX_PDF_PAGES,
) -> PdfWorkerResult:
    """Run the fixed guarded PDF parser with its established public result API."""
    return _run_pdf_worker(source, limits, max_pages, None)


def run_observed_pdf_worker(
    source: bytes,
    limits: WorkerLimits | None = None,
    max_pages: int = MAX_PDF_PAGES,
) -> WorkerExecution[PdfWorkerResult]:
    """Return a completed PDF result with actual combined transport consumption."""
    counter = WorkerOutputCounter()
    result = _run_pdf_worker(source, limits, max_pages, counter.observe)
    return WorkerExecution(result, counter.output_bytes)
