"""Validate independent PDF reference metadata without importing a PDF parser."""

from typing import Literal, cast

from .corpus_constants import MAX_PDF_CORPUS_PAGES
from .corpus_error import CorpusError
from .manifest_fields import (
    FIXTURE_FIELDS,
    annotation_values,
    exact_fields,
    nonempty_text,
    nonnegative_integer,
    parse_fixture_metadata,
)
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_fact_annotation import PdfFactAnnotation

_PDF_FIXTURE_FIELDS = FIXTURE_FIELDS | {"page_count"}
_ANNOTATION_FIELDS = frozenset(("page_number", "quote"))


def _annotation(value: object, page_count: int) -> PdfFactAnnotation:
    fields = exact_fields(value, _ANNOTATION_FIELDS)
    page_number = nonnegative_integer(fields["page_number"])
    if not 1 <= page_number <= page_count:
        raise CorpusError("invalid_manifest")
    return PdfFactAnnotation(page_number, nonempty_text(fields["quote"]))


def parse_pdf_fixture(value: object) -> PdfCorpusFixture:
    """Retain declared page counts and facts without claiming recovered evidence."""
    fields = exact_fields(value, _PDF_FIXTURE_FIELDS)
    fixture_id, path, sha256, language, author_label, subject_label = parse_fixture_metadata(
        fields, "pdf"
    )
    page_count = nonnegative_integer(fields["page_count"])
    if not 1 <= page_count <= MAX_PDF_CORPUS_PAGES:
        raise CorpusError("invalid_manifest")
    outcome = nonempty_text(fields["outcome"])
    if outcome not in ("success", "no_text", "encrypted_pdf", "malformed_input"):
        raise CorpusError("invalid_manifest")
    annotations = annotation_values(fields["annotations"], outcome)
    return PdfCorpusFixture(
        fixture_id=fixture_id,
        path=path,
        sha256=sha256,
        format="pdf",
        language=language,
        author_label=author_label,
        subject_label=subject_label,
        outcome=cast(Literal["success", "no_text", "encrypted_pdf", "malformed_input"], outcome),
        annotations=tuple(_annotation(annotation, page_count) for annotation in annotations),
        page_count=page_count,
    )
