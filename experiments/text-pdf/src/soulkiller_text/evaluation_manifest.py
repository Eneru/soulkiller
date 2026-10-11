"""Select a strict bounded synthetic TXT/PDF evaluation corpus without I/O."""

from .corpus_constants import MAX_PDF_CORPUS_PAGES
from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .manifest_fields import manifest_fields, validate_unique_fixtures
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_manifest import parse_pdf_fixture
from .text_manifest import parse_text_fixture


def _fixture(value: object, version: int) -> CorpusFixture | PdfCorpusFixture:
    if version == 2 and isinstance(value, dict) and value.get("format") == "pdf":
        return parse_pdf_fixture(value)
    return parse_text_fixture(value)


def parse_evaluation_manifest(source: bytes) -> tuple[CorpusFixture | PdfCorpusFixture, ...]:
    """Accept version-1 TXT and version-2 mixed metadata before any fixture reads.

    PDF declarations are independent reference metadata, not extraction results.
    """
    version, fixtures = manifest_fields(source, (1, 2))
    result = tuple(_fixture(fixture, version) for fixture in fixtures)
    validate_unique_fixtures((fixture.fixture_id, fixture.path) for fixture in result)
    page_count = sum(
        fixture.page_count for fixture in result if isinstance(fixture, PdfCorpusFixture)
    )
    if page_count > MAX_PDF_CORPUS_PAGES:
        raise CorpusError("invalid_manifest")
    return result
