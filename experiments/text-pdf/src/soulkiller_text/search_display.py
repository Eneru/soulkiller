"""Terminal-safe readable search results and exact escaped JSON."""

import json
from dataclasses import asdict

from .extraction_display import safe_display
from .search_constants import UNFINISHED_OUTCOME, UNKNOWN_OUTCOME
from .search_coverage import SearchCoverage
from .search_report import SearchReport
from .source_match import SourceMatch


def _pages(pages: tuple[int, ...] | None) -> str:
    """Distinguish unknown page coverage from a known empty list in the readable report."""
    if pages is None:
        return "unknown"
    return ", ".join(str(page) for page in pages) if pages else "none"


def _coverage_line(coverage: SearchCoverage) -> str:
    """Describe each document's actual coverage without exposing Python container notation."""
    availability = "retained text" if coverage.text_available else "no retained text"
    if coverage.outcome in (UNKNOWN_OUTCOME, UNFINISHED_OUTCOME):
        availability = "text unavailable"
    parts = [f"{coverage.fixture_id} ({coverage.path}): {coverage.outcome}", availability]
    if coverage.unfinished_reason is not None:
        parts.append(f"stopped: {coverage.unfinished_reason}")
    if coverage.format == "pdf":
        total = "unknown" if coverage.total_pages is None else str(coverage.total_pages)
        parts.extend(
            (
                f"retained pages: {_pages(coverage.retained_pages)}; total pages: {total}",
                f"missing pages: {_pages(coverage.missing_pages)}",
            )
        )
    return "; ".join(parts)


def _match_lines(match: SourceMatch) -> list[str]:
    """Show separately resolving match/context spans with declared source attribution."""
    location = "TXT" if match.page_number is None else f"PDF page {match.page_number}"
    return [
        f"{match.fixture_id} ({match.path}) — {location}",
        f"SHA-256: {match.source_sha256}",
        f"Format: {match.format}; language: {match.language}; "
        f"declared author: {match.author_label}; declared subject: {match.subject_label}",
        f"Match [{match.match_start}, {match.match_end}); "
        f"excerpt [{match.excerpt_start}, {match.excerpt_end})",
        match.excerpt,
    ]


def render_search(report: SearchReport, *, as_json: bool) -> str:
    """Escape controls for terminal output while JSON preserves exact query/evidence values."""
    if as_json:
        return json.dumps(asdict(report), ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    lines = [
        f"Run status: {report.status}",
        f"Query: {report.query!r} (case-sensitive literal substring)",
        f"Returned matches: {len(report.matches)}; limit: {report.limit}; "
        f"additional matches exist: {report.more_matches}",
        "Order: manifest, physical page, offset; no relevance or truth ranking.",
        "Offsets: zero-based, end-exclusive code points in saved TXT or the named PDF page.",
        "Declared source labels do not establish identity or truth.",
        "Document coverage:",
    ]
    lines.extend(_coverage_line(coverage) for coverage in report.coverage)
    if not report.matches:
        lines.append("No matching passage was found for this literal query.")
    for match in report.matches:
        lines.extend(_match_lines(match))
    return safe_display("\n".join(lines))
