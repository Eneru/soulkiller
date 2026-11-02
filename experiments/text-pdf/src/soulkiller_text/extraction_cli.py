"""Manual run/show commands for the synthetic extraction example."""

import argparse
import sys
from pathlib import Path

from .corpus_error import CorpusError
from .extraction_display import render_saved
from .manual_cli_constants import CANCELLED, DEFAULT_CORPUS, FAILURE, SUCCESS
from .run_status import RunStatus
from .run_store_error import RunStoreError
from .saved_run import run_saved_corpus
from .saved_run_reader import read_saved_run


def _arguments(arguments: list[str] | None) -> argparse.Namespace:
    """Parse a small explicit interface; argparse handles usage errors before any writes."""
    parser = argparse.ArgumentParser(description="Run and inspect synthetic TXT/PDF extraction.")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "show"):
        child = commands.add_parser(command)
        child.add_argument("--run-id", required=True)
        child.add_argument("--corpus", default=DEFAULT_CORPUS)
        if command == "show":
            child.add_argument("--json", action="store_true")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    """Run the selected operation with safe failures and no raw source/path diagnostics."""
    args = _arguments(arguments)
    try:
        if args.command == "run":
            run_saved_corpus(Path.cwd(), args.corpus, args.run_id)
        status, rows = read_saved_run(Path.cwd(), args.corpus, args.run_id)
        print(render_saved(status, rows, as_json=getattr(args, "json", False)))
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
