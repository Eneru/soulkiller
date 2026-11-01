"""Independent immutable rows and literal JSON oracles for fixture records."""

import hashlib
import json
from dataclasses import replace
from typing import Literal

from soulkiller_text.corpus_fixture import CorpusFixture
from soulkiller_text.fixture_run import FixtureRun
from soulkiller_text.pdf_corpus_fixture import PdfCorpusFixture
from soulkiller_text.pdf_page import PdfPage
from soulkiller_text.pdf_worker_outcome import PdfWorkerOutcome
from soulkiller_text.pdf_worker_result import PdfWorkerResult
from soulkiller_text.worker_outcome import WorkerOutcome
from soulkiller_text.worker_result import WorkerResult

from .synthetic_sources import BILINGUAL_SHA256, BILINGUAL_TEXT

PAYLOAD_BYTES = 10 * 1024 * 1024 - 48
PROBE_BYTES = 10 * 1024 * 1024 + 1
PDF_HASH = "d" * 64


def text_specification() -> CorpusFixture:
    """Declare invented metadata whose source path need never exist."""
    return CorpusFixture(
        "text-fr",
        "never-opened/notes.txt",
        BILINGUAL_SHA256,
        "txt",
        "fr",
        "  Invented author  ",
        "Invented subject",
        "success",
        (),
    )


def pdf_specification() -> PdfCorpusFixture:
    """Declare a two-page PDF independently of extraction and source I/O."""
    return PdfCorpusFixture(
        "pdf-en",
        "never-opened/notes.pdf",
        PDF_HASH,
        "pdf",
        "en",
        "Invented author",
        "Invented subject",
        "success",
        (),
        2,
    )


def text_row() -> FixtureRun:
    """Return a fresh successful row with exact bilingual Unicode and line endings."""
    specification = text_specification()
    result = WorkerResult(WorkerOutcome.SUCCESS, specification.sha256, BILINGUAL_TEXT)
    return FixtureRun(specification, result, 157)


def pdf_row() -> FixtureRun:
    """Retain one nonempty and one blank physical page as independent evidence."""
    specification = pdf_specification()
    result = PdfWorkerResult(
        PdfWorkerOutcome.SUCCESS,
        specification.sha256,
        (PdfPage(1, "Corin garde un café.\r\nAn invented fact."), PdfPage(2, "")),
        2,
        (),
    )
    return FixtureRun(specification, result, 211)


def text_document() -> dict[str, object]:
    """Build the declared public wire format without using the production encoder."""
    return {
        "schema_version": 1,
        "fixture_id": "text-fr",
        "format": "txt",
        "source_sha256": BILINGUAL_SHA256,
        "result": {"outcome": "success", "text": BILINGUAL_TEXT},
        "output_bytes": 157,
        "unfinished_reason": None,
    }


def pdf_document() -> dict[str, object]:
    """Provide literal PDF wire values including exact physical-page text."""
    return {
        "schema_version": 1,
        "fixture_id": "pdf-en",
        "format": "pdf",
        "source_sha256": PDF_HASH,
        "result": {
            "outcome": "success",
            "pages": [
                {"page_number": 1, "text": "Corin garde un café.\r\nAn invented fact."},
                {"page_number": 2, "text": ""},
            ],
            "total_pages": 2,
            "missing_pages": [],
        },
        "output_bytes": 211,
        "unfinished_reason": None,
    }


def wire(document: object) -> bytes:
    """Encode independently authored JSON, including deliberately invalid values."""
    return json.dumps(document, ensure_ascii=True, separators=(",", ":")).encode("ascii")


def exact_payload_document(extra: int = 0, character: str = "x") -> dict[str, object]:
    """Fill a literal wire envelope to the frame-adjusted byte ceiling."""
    document = text_document()
    result = {"outcome": "success", "text": ""}
    document["result"] = result
    overhead = len(wire(document))
    width = len(json.dumps(character, ensure_ascii=True)) - 2
    count, remainder = divmod(PAYLOAD_BYTES + extra - overhead, width)
    result["text"] = character * count + "x" * remainder
    return document


def failed_text_row(outcome: WorkerOutcome) -> FixtureRun:
    """Keep the declared expectation distinct from a completed failed observation."""
    row = text_row()
    return replace(row, result=WorkerResult(outcome, row.specification.sha256, None))


def failed_pdf_row(outcome: PdfWorkerOutcome) -> FixtureRun:
    """Return empty unavailable evidence for one completed supervised PDF failure."""
    row = pdf_row()
    return replace(row, result=PdfWorkerResult(outcome, row.specification.sha256, (), None, ()))


def source_specification(
    source: bytes, kind: Literal["txt", "pdf"]
) -> CorpusFixture | PdfCorpusFixture:
    """Bind a synthetic real-worker source to independently declared fixture metadata."""
    specification = text_specification() if kind == "txt" else pdf_specification()
    return replace(specification, sha256=hashlib.sha256(source).hexdigest())
