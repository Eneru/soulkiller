"""Bounded physical page records and coverage/outcome invariants."""

from .pdf_page import PdfPage
from .pdf_worker_outcome import PdfWorkerOutcome


def decode_pages(value: object, max_pages: int) -> tuple[PdfPage, ...]:
    """Preserve exact page text while excluding malformed Unicode and numbering."""
    if not isinstance(value, list) or len(value) > max_pages:
        raise ValueError("invalid_worker_response")
    pages: list[PdfPage] = []
    previous = 0
    for record in value:
        if not isinstance(record, dict) or set(record) != {"page_number", "text"}:
            raise ValueError("invalid_worker_response")
        number = record["page_number"]
        text = record["text"]
        if type(number) is not int or not previous < number <= max_pages:
            raise ValueError("invalid_worker_response")
        if not isinstance(text, str) or any(0xD800 <= ord(char) <= 0xDFFF for char in text):
            raise ValueError("invalid_worker_response")
        pages.append(PdfPage(number, text))
        previous = number
    return tuple(pages)


def decode_missing(value: object, max_pages: int) -> tuple[int, ...]:
    """Reject booleans, duplicates, disorder and unbounded missing-page lists."""
    if not isinstance(value, list) or len(value) > max_pages:
        raise ValueError("invalid_worker_response")
    missing: list[int] = []
    previous = 0
    for number in value:
        if type(number) is not int or not previous < number <= max_pages:
            raise ValueError("invalid_worker_response")
        missing.append(number)
        previous = number
    return tuple(missing)


def decode_count(value: object) -> int | None:
    """Keep unknown counts distinct from complete zero-page documents."""
    if value is None:
        return None
    if type(value) is not int or value < 0:
        raise ValueError("invalid_worker_response")
    return value


def _validate_partition(
    pages: tuple[PdfPage, ...], missing: tuple[int, ...], total: int | None, max_pages: int
) -> None:
    if total is None or total > max_pages:
        if pages or missing:
            raise ValueError("invalid_worker_response")
        return
    covered_numbers = {page.page_number for page in pages}
    missing_numbers = set(missing)
    if covered_numbers & missing_numbers:
        raise ValueError("invalid_worker_response")
    if covered_numbers | missing_numbers != set(range(1, total + 1)):
        raise ValueError("invalid_worker_response")


def validate_evidence(
    outcome: PdfWorkerOutcome,
    pages: tuple[PdfPage, ...],
    total: int | None,
    missing: tuple[int, ...],
    max_pages: int,
) -> None:
    """Accept only evidence consistent with complete, partial or failed extraction."""
    _validate_partition(pages, missing, total, max_pages)
    meaningful = any(page.text.strip() for page in pages)
    if outcome == PdfWorkerOutcome.PAGE_LIMIT:
        valid = total is not None and total > max_pages
    elif total is not None and total > max_pages:
        valid = False
    elif outcome == PdfWorkerOutcome.ENCRYPTED_PDF:
        valid = total is None
    elif outcome == PdfWorkerOutcome.SUCCESS:
        valid = total is not None and not missing and meaningful
    elif outcome == PdfWorkerOutcome.NO_TEXT:
        valid = total is not None and not missing and not meaningful
    elif outcome == PdfWorkerOutcome.PARTIAL:
        valid = total is not None and bool(pages) and bool(missing)
    else:
        valid = total is None or (not pages and bool(missing))
    if not valid:
        raise ValueError("invalid_worker_response")
