"""Human-readable saved evidence with terminal control sequences escaped."""

import json

from .fixture_record import encode_fixture_record
from .fixture_run import FixtureRun
from .pdf_worker_result import PdfWorkerResult
from .run_status import RunStatus


def safe_display(text: str) -> str:
    """Keep readable Unicode/newlines while escaping terminal controls and bidi formatting."""
    return "".join(c if c.isprintable() or c in "\n\t" else f"\\u{ord(c):04x}" for c in text)


def _row_text(index: int, row: FixtureRun | None) -> list[str]:
    """Render a source reference and its exact text or explicit unavailable/error state."""
    if row is None:
        return [f"Document {index}: not saved; execution state unknown."]
    spec = row.specification
    result = row.result
    outcome = result.outcome.value if result is not None else f"unfinished: {row.unfinished_reason}"
    lines = [f"{index}. {spec.fixture_id} ({spec.path}) — {outcome}", f"SHA-256: {spec.sha256}"]
    if isinstance(result, PdfWorkerResult):
        lines.extend(f"[Page {page.page_number}]\n{page.text}" for page in result.pages)
        if result.missing_pages:
            lines.append(f"Missing pages: {result.missing_pages}")
    elif result is not None and result.text is not None:
        lines.append(result.text)
    return lines


def render_saved(
    status: RunStatus | None, rows: tuple[FixtureRun | None, ...], *, as_json: bool
) -> str:
    """Produce text or escaped exact-evidence JSON without executing sources."""
    label = status.value if status is not None else "incomplete"
    if as_json:
        return json.dumps(
            {
                "status": label,
                "fixtures": [
                    None if row is None else json.loads(encode_fixture_record(row)) for row in rows
                ],
            },
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    lines = [
        f"Run status: {label}",
        "Complete means scheduling ended; individual errors remain below.",
    ]
    for index, row in enumerate(rows, start=1):
        lines.extend(_row_text(index, row))
        lines.append("")
    return safe_display("\n".join(lines))


def render_score(report: dict[str, object], *, as_json: bool) -> str:
    """Render bounded reference checks with escaped terminal controls or exact JSON."""
    if as_json:
        return json.dumps(report, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    lines = [
        f"Run status: {report['status']}",
        f"Exact quote recovery: {report['recovered_facts']}/{report['expected_facts']}",
        f"Correct reference locations: {report['correct_locations']}/{report['expected_facts']}",
        f"Expected outcome matches: {report['outcome_matches']}/{report['expected_outcomes']}",
        f"Documents without reference facts: {report['unannotated_documents']}",
        f"Matching: {report['matching']}",
        "No semantic, reading-order, performance or acceptance-threshold evaluation.",
    ]
    documents = report["documents"]
    if not isinstance(documents, list):
        raise ValueError("invalid_score_report")
    for document in documents:
        lines.append(
            f"{document['fixture_id']}: expected {document['expected_outcome']}, "
            f"observed {document['observed_outcome']}"
        )
        lines.append(f"SHA-256: {document['source_sha256']}")
        for fact in document["facts"]:
            lines.append(
                f"  {fact['quote']!r}: expected (page, start, end) "
                f"{fact['expected_location']}; observed {fact['observed_location']}; "
                f"location matched: {fact['location_matched']}"
            )
    return safe_display("\n".join(lines))
