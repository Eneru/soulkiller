"""Bounded search observations, distinct from a generated answer or ranking."""

from dataclasses import dataclass

from .search_coverage import SearchCoverage
from .source_match import SourceMatch


@dataclass(frozen=True)
class SearchReport:
    """The additional-match flag proves truncation without claiming an exact total."""

    status: str
    query: str
    limit: int
    matches: tuple[SourceMatch, ...]
    more_matches: bool
    coverage: tuple[SearchCoverage, ...]
