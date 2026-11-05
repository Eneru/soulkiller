"""Manual extraction and saved-reference commands for the synthetic extraction example."""

import argparse
import sys
from functools import partial
from pathlib import Path

from .answer_display import render_answer
from .corpus_error import CorpusError
from .corpus_fixture import CorpusFixture
from .dialogue import ask_saved, validate_question
from .dialogue_constants import DIALOGUE_CORPUS, PERSONA_ID
from .dialogue_error import DialogueError
from .extraction_display import render_saved, render_score
from .extraction_scoring import score_extraction
from .fixture_run import FixtureRun
from .manual_cli_constants import CANCELLED, DEFAULT_CORPUS, FAILURE, SUCCESS
from .pdf_corpus_fixture import PdfCorpusFixture
from .run_status import RunStatus
from .run_store_error import RunStoreError
from .saved_run import run_saved_corpus
from .saved_run_reader import read_saved_evaluation
from .scripted_model import DEMO_CASES, demo_completion
from .search_constants import DEFAULT_SEARCH_LIMIT
from .search_display import render_search
from .search_report import SearchReport
from .source_search import search_evidence, validate_search


def _ask_arguments(child: argparse.ArgumentParser) -> None:
    """Expose the approved fixed profile and explicit scripted-backend choice."""
    child.add_argument("--profile", choices=(PERSONA_ID,), required=True)
    child.add_argument("--question", required=True)
    child.add_argument("--evidence-query", required=True)
    child.add_argument("--language", choices=("fr", "en"), required=True)
    child.add_argument(
        "--demo-case",
        choices=DEMO_CASES,
        required=True,
        help="Explicit scripted response; no LLM is called.",
    )


def _arguments(arguments: list[str] | None) -> argparse.Namespace:
    """Parse a small explicit interface; argparse handles usage errors before any writes."""
    parser = argparse.ArgumentParser(description="Run and inspect synthetic TXT/PDF extraction.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "show", "score", "search", "ask"):
        child = commands.add_parser(command)
        child.add_argument("--run-id", required=True)
        child.add_argument("--corpus")
        if command != "run":
            child.add_argument("--json", action="store_true")
        if command == "search":
            child.description = (
                "Search a case-sensitive literal substring; no semantic query syntax."
            )
            child.add_argument("--query", required=True, help="Exact case, accents and whitespace.")
            child.add_argument("--limit", type=int, default=DEFAULT_SEARCH_LIMIT)
        if command == "ask":
            _ask_arguments(child)
    args = parser.parse_args(arguments)
    if args.corpus is None:
        args.corpus = DIALOGUE_CORPUS if args.command == "ask" else DEFAULT_CORPUS
    if args.command == "ask":
        try:
            validate_question(args.profile, args.question, args.evidence_query, args.language)
        except ValueError as error:
            parser.error(str(error))
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


def _announce_evidence(report: SearchReport) -> None:
    """Disclose complete eligible coverage before invoking the model, keeping stdout JSON clean."""
    print(
        f"Evidence: {len(report.coverage)} eligible documents; "
        f"{len(report.matches)} matching passages from the complete saved run.",
        file=sys.stderr,
        flush=True,
    )


def _ask_text(args: argparse.Namespace) -> str:
    """Run the fully explicit scripted collaborator and return safe text/JSON presentation."""
    result = ask_saved(
        Path.cwd(),
        args.corpus,
        args.run_id,
        args.profile,
        args.question,
        args.evidence_query,
        args.language,
        partial(demo_completion, case=args.demo_case, language=args.language),
        on_evidence=_announce_evidence,
    )
    return render_answer(result, as_json=args.json)


def main(arguments: list[str] | None = None) -> int:
    """Run the selected operation with safe failures and no raw source/path diagnostics."""
    args = _arguments(arguments)
    try:
        if args.command == "ask":
            print(_ask_text(args))
            return SUCCESS
        if args.command == "run":
            run_saved_corpus(Path.cwd(), args.corpus, args.run_id)
        status, specifications, rows = read_saved_evaluation(Path.cwd(), args.corpus, args.run_id)
        print(_render(args, status, specifications, rows))
        if args.command == "run":
            print(f"Saved under .soulkiller-local/evaluation/{args.run_id}/")
        if status is RunStatus.CANCELLED:
            return CANCELLED
        return SUCCESS if status is RunStatus.COMPLETE else FAILURE
    except (CorpusError, RunStoreError, DialogueError, ValueError) as error:
        category = (
            error.category
            if isinstance(error, (CorpusError, RunStoreError, DialogueError))
            else "invalid_saved_run"
        )
        if str(error) == "offline_environment_required":
            category = (
                "Offline container required: launch with --network none --memory 3g --cpus 2."
            )
        label = "Dialogue" if args.command == "ask" else "Extraction"
        print(f"{label} failed: {category}", file=sys.stderr)
        return FAILURE
    except KeyboardInterrupt:
        print("Interrupted; use show to inspect any saved progress.", file=sys.stderr)
        return CANCELLED
