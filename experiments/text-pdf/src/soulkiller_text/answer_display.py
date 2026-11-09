"""Keep scripted/generated text visibly distinct from exact local source excerpts."""

import json
from dataclasses import asdict

from .answer_result import AnswerResult
from .dialogue_constants import DEMO_BACKEND, NO_BACKEND
from .extraction_display import safe_display


def render_answer(result: AnswerResult, *, as_json: bool) -> str:
    """Render accepted citations and escape controls; model quotations are never trusted."""
    if as_json:
        return json.dumps(asdict(result), ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    lines = [
        f"Backend: {result.backend}",
        f"Answer status: {result.status}",
        "Response text:",
        result.text,
        "Exact local sources (citation resolution does not prove factual support):",
    ]
    if result.backend == DEMO_BACKEND:
        lines.insert(1, "Scripted demo only: no LLM interpretation or measured answer quality.")
    elif result.backend != NO_BACKEND:
        lines.insert(1, "Generated local trial response. Inspect the cited source excerpts.")
    for index, source in enumerate(result.sources, start=1):
        if f"S{index}" not in result.citations:
            continue
        page = "TXT" if source.page_number is None else f"PDF page {source.page_number}"
        lines.extend(
            [
                f"[S{index}] {source.fixture_id} ({source.path}) — {page}",
                f"SHA-256: {source.source_sha256}",
                f"Declared author: {source.author_label}; subject: {source.subject_label}",
                f"Excerpt [{source.excerpt_start}, {source.excerpt_end}):",
                source.excerpt,
            ]
        )
    return safe_display("\n".join(lines))
