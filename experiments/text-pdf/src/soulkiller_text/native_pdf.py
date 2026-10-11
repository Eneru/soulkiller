"""Internal sequential native adapter; callers must supply the execution boundary."""

from __future__ import annotations

import logging
from hashlib import sha256
from io import BytesIO
from typing import TYPE_CHECKING

from .corpus_constants import MAX_SOURCE_BYTES
from .pdf_constants import MAX_PDF_PAGES
from .pdf_outcome import PdfOutcome
from .pdf_page import PdfPage
from .pdf_result import PdfResult

if TYPE_CHECKING:
    from pypdf import PdfReader


def _validate_input(source: bytes, max_pages: int) -> None:
    if type(source) is not bytes:
        raise TypeError("invalid_pdf_source")
    if len(source) > MAX_SOURCE_BYTES:
        raise ValueError("pdf_input_too_large")
    if type(max_pages) is not int or not 1 <= max_pages <= MAX_PDF_PAGES:
        raise ValueError("invalid_pdf_page_limit")


def _open_reader(source: bytes) -> PdfReader | PdfOutcome:
    """Load the optional parser lazily and suppress its sensitive diagnostics."""
    try:
        from pypdf.errors import DependencyError, PdfReadError
    except ImportError:
        return PdfOutcome.UNSUPPORTED_DEPENDENCY
    except MemoryError:
        raise
    except Exception:
        return PdfOutcome.CANDIDATE_FAILURE
    try:
        from pypdf import PdfReader, overwrite_configuration

        overwrite_configuration(jbig2dec_binary=None, disable_legacy_handling=True)
        logger = logging.getLogger("pypdf")
        logger.handlers = [logging.NullHandler()]
        logger.propagate = False
        return PdfReader(BytesIO(source), strict=False, password=None)
    except (ImportError, DependencyError):
        return PdfOutcome.UNSUPPORTED_DEPENDENCY
    except PdfReadError:
        return PdfOutcome.MALFORMED_INPUT
    except MemoryError:
        raise
    except Exception:
        return PdfOutcome.CANDIDATE_FAILURE


def _inspect_reader(reader: PdfReader) -> int | PdfOutcome:
    from pypdf.errors import DependencyError, PdfReadError

    try:
        if reader.is_encrypted:
            return PdfOutcome.ENCRYPTED_PDF
        return len(reader.pages)
    except DependencyError:
        return PdfOutcome.UNSUPPORTED_DEPENDENCY
    except PdfReadError:
        return PdfOutcome.MALFORMED_INPUT
    except MemoryError:
        raise
    except Exception:
        return PdfOutcome.CANDIDATE_FAILURE


def _page_text(reader: PdfReader, index: int) -> str:
    text: object = reader.pages[index].extract_text(extraction_mode="plain")
    if text is None:
        return ""
    if not isinstance(text, str):
        raise ValueError("invalid_candidate_text")
    return text


def _page_failure(error: Exception) -> PdfOutcome:
    from pypdf.errors import DependencyError, PdfReadError

    if isinstance(error, DependencyError):
        return PdfOutcome.UNSUPPORTED_DEPENDENCY
    if isinstance(error, PdfReadError):
        return PdfOutcome.MALFORMED_INPUT
    return PdfOutcome.CANDIDATE_FAILURE


def _failed_document_outcome(failures: set[PdfOutcome]) -> PdfOutcome:
    if len(failures) == 1:
        return next(iter(failures))
    return PdfOutcome.CANDIDATE_FAILURE


def _extract_pages(reader: PdfReader, count: int, source_hash: str) -> PdfResult:
    pages: list[PdfPage] = []
    missing: list[int] = []
    failures: set[PdfOutcome] = set()
    for index in range(count):
        try:
            page = PdfPage(index + 1, _page_text(reader, index))
        except MemoryError:
            raise
        except Exception as error:
            missing.append(index + 1)
            failures.add(_page_failure(error))
        else:
            pages.append(page)
    if missing:
        outcome = PdfOutcome.PARTIAL if pages else _failed_document_outcome(failures)
    else:
        outcome = (
            PdfOutcome.SUCCESS if any(page.text.strip() for page in pages) else PdfOutcome.NO_TEXT
        )
    return PdfResult(outcome, source_hash, tuple(pages), count, tuple(missing))


def extract_native_pdf(source: bytes, max_pages: int = MAX_PDF_PAGES) -> PdfResult:
    """Extract trusted synthetic bytes; this seam does not supervise/isolate parsing."""
    _validate_input(source, max_pages)
    source_hash = sha256(source).hexdigest()
    reader = _open_reader(source)
    if isinstance(reader, PdfOutcome):
        return PdfResult(reader, source_hash, (), None, ())
    count = _inspect_reader(reader)
    if isinstance(count, PdfOutcome):
        return PdfResult(count, source_hash, (), None, ())
    if count > max_pages:
        return PdfResult(PdfOutcome.PAGE_LIMIT, source_hash, (), count, ())
    return _extract_pages(reader, count, source_hash)
