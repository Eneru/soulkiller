"""Observed document coverage retained even when no passage matches."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchCoverage:
    """None means unknown/not applicable; empty page tuples mean known empty coverage."""

    fixture_id: str
    path: str
    format: str
    outcome: str
    unfinished_reason: str | None
    text_available: bool
    retained_pages: tuple[int, ...] | None
    total_pages: int | None
    missing_pages: tuple[int, ...] | None
