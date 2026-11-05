"""Manual extraction and saved-reference commands for the synthetic extraction example."""

import argparse
import sys
from pathlib import Path

from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .extraction_display import render_saved, render_score
from .extraction_scoring import score_extraction
from .fixture_run import FixtureRun
from .manual_cli_constants import CANCELLED, DEFAULT_CORPUS, FAILURE, SUCCESS
from .pdf_corpus_fixture import PdfCorpusFixture
from .run_status import RunStatus
from .run_store_error import RunStoreError
from .saved_run import run_saved_corpus
from .saved_run_reader import read_saved_evaluation
from .search_constants import DEFAULT_SEARCH_LIMIT
from .search_display import render_search
from .source_search import search_evidence, validate_search


def _arguments(arguments: list[str] | None) -> argparse.Namespace:
    """Parse a small explicit interface; argparse handles usage errors before any writes."""
    parser = argparse.ArgumentParser(description="Run and inspect synthetic TXT/PDF extraction.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "show", "score", "search"):
        child = commands.add_parser(command)
        child.add_argument("--run-id", required=True)
        child.add_argument("--corpus", default=DEFAULT_CORPUS)
        if command != "run":
            child.add_argument("--json", action="store_true")
        if command == "search":
            child.description = (
                "Search a case-sensitive literal substring; no semantic query syntax."
            )
            child.add_argument("--query", required=True, help="Exact case, accents and whitespace.")
            child.add_argument("--limit", type=int, default=DEFAULT_SEARCH_LIMIT)
    args = parser.parse_args(arguments)
    if args.command == "search":
        try:
            validate_search(args.query, args.limit)
        except ValueError as error:
            parser.error(str(error))
    return args


def _render(
    args: argparse.Namespace,
    status: RunStatus | None,
    specifications: tuple[CorpusFixture | PdfCorpusFixture, ...],
    rows: tuple[FixtureRun | None, ...],
) -> str:
    """Dispatch presentation without side effects; all rows were validated before this phase."""
    if args.command == "score":
        return render_score(score_extraction(status, specifications, rows), as_json=args.json)
    if args.command == "search":
        report = search_evidence(status, specifications, rows, args.query, args.limit)
        return render_search(report, as_json=args.json)
    return render_saved(status, rows, as_json=getattr(args, "json", False))


def main(arguments: list[str] | None = None) -> int:
    """Run the selected operation with safe failures and no raw source/path diagnostics."""
    args = _arguments(arguments)
    try:
        if args.command == "run":
            run_saved_corpus(Path.cwd(), args.corpus, args.run_id)
        status, specifications, rows = read_saved_evaluation(Path.cwd(), args.corpus, args.run_id)
        print(_render(args, status, specifications, rows))
        if args.command == "run":
            print(f"Saved under .soulkiller-local/evaluation/{args.run_id}/")
        if status is RunStatus.CANCELLED:
            return CANCELLED
        return SUCCESS if status is RunStatus.COMPLETE else FAILURE
    except (CorpusError, RunStoreError, ValueError) as error:
        category = (
            error.category
            if isinstance(error, (CorpusError, RunStoreError))
            else "invalid_saved_run"
        )
        if str(error) == "offline_environment_required":
            category = (
                "Offline container required: launch with --network none --memory 3g --cpus 2."
            )
        print(f"Extraction failed: {category}", file=sys.stderr)
        return FAILURE
    except KeyboardInterrupt:
        print("Interrupted; use show to inspect any saved progress.", file=sys.stderr)
        return CANCELLED
