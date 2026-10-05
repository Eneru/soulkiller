"""The exact verified bytes associated with manifest metadata."""

from dataclasses import dataclass

from .corpus_fixture import CorpusFixture


@dataclass(frozen=True)
class LoadedFixture:
    """Retain a source snapshot so extraction need not reopen a path."""

    specification: CorpusFixture
    source: bytes
