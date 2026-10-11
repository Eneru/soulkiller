"""Validate bounded version-1 synthetic TXT manifests without source-file I/O."""

from .corpus_fixture import CorpusFixture
from .manifest_fields import manifest_fields, validate_unique_fixtures
from .text_manifest import parse_text_fixture


def parse_manifest(source: bytes) -> tuple[CorpusFixture, ...]:
    """Validate schema version 1, returning immutable TXT metadata without I/O.

    CorpusError categories are manifest_too_large, invalid_manifest,
    invalid_path and duplicate_fixture. Messages never include input data.
    """
    _, fixtures = manifest_fields(source, (1,))
    result = tuple(parse_text_fixture(fixture) for fixture in fixtures)
    validate_unique_fixtures((fixture.fixture_id, fixture.path) for fixture in result)
    return result
