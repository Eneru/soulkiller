"""Validate a complete explicit TXT corpus before returning verified snapshots."""

from pathlib import Path

from .confined_files import corpus_descriptor, read_confined
from .corpus_constants import MAX_MANIFEST_BYTES, MAX_SOURCE_BYTES
from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .evidence_slice import evidence_slice
from .extract_utf8 import extract_utf8
from .loaded_fixture import LoadedFixture
from .manifest_validation import parse_manifest


def _load_fixture(root: int, fixture: CorpusFixture) -> LoadedFixture:
    source = read_confined(root, fixture.path, MAX_SOURCE_BYTES)
    result = extract_utf8(source)
    if result.source_sha256 != fixture.sha256:
        raise CorpusError("source_mismatch")
    if result.outcome != fixture.outcome:
        raise CorpusError("expectation_mismatch")
    for annotation in fixture.annotations:
        try:
            evidence = evidence_slice(result, annotation.start, annotation.end)
        except (TypeError, ValueError):
            raise CorpusError("expectation_mismatch") from None
        if evidence.quote != annotation.quote:
            raise CorpusError("expectation_mismatch")
    return LoadedFixture(fixture, source)


def load_corpus(workspace_root: Path, corpus_path: str) -> tuple[LoadedFixture, ...]:
    """The workspace anchor is trusted caller configuration, not a manifest field."""
    with corpus_descriptor(workspace_root, corpus_path) as root:
        try:
            manifest = read_confined(root, "manifest.json", MAX_MANIFEST_BYTES)
        except CorpusError as error:
            if error.category == "input_too_large":
                raise CorpusError("manifest_too_large") from None
            raise
        fixtures = parse_manifest(manifest)
        return tuple(_load_fixture(root, fixture) for fixture in fixtures)
