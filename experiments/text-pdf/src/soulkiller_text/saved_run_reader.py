"""Inspect bounded saved rows independently of current source-file contents."""

from pathlib import Path

from .corpus_run_result import CorpusRunResult
from .evaluation_manifest import parse_evaluation_manifest
from .fixture_record import decode_fixture_record
from .fixture_run import FixtureRun
from .run_constants import MAX_RUN_OUTPUT_BYTES
from .run_status import RunStatus
from .run_store import RunStore, open_run_store
from .run_store_error import RunStoreError
from .saved_json import INVALID_SAVED_RUN, decode_saved


def _optional(store: RunStore, name: str) -> bytes | None:
    """Treat only unavailable records as missing; corruption and unsafe links still fail."""
    try:
        return store.read_record(name)
    except RunStoreError as error:
        if error.category != "record_unavailable":
            raise
        return None


def _summary(payload: bytes, rows: tuple[FixtureRun | None, ...]) -> CorpusRunResult:
    """Validate final status, complete row coverage and independently summed observations."""
    fields = decode_saved(payload)
    if set(fields) != {"version", "status", "output_bytes"} or type(fields["version"]) is not int:
        raise ValueError(INVALID_SAVED_RUN)
    if fields["version"] != 1 or type(fields["status"]) is not str or any(r is None for r in rows):
        raise ValueError(INVALID_SAVED_RUN)
    try:
        status = RunStatus(fields["status"])
    except ValueError:
        raise ValueError(INVALID_SAVED_RUN) from None
    records = tuple(row for row in rows if row is not None)
    count = fields["output_bytes"]
    observed = (
        None
        if any(r.output_bytes is None for r in records)
        else sum(r.output_bytes for r in records if r.output_bytes is not None)
    )
    if count is not None and (type(count) is not int or not 0 <= count <= MAX_RUN_OUTPUT_BYTES + 1):
        raise ValueError(INVALID_SAVED_RUN)
    if count != observed or any(
        r.unfinished_reason is not None and r.unfinished_reason is not status for r in records
    ):
        raise ValueError(INVALID_SAVED_RUN)
    unfinished = False
    unknown = 0
    for row in records:
        if row.result is None:
            unfinished = True
            unknown += row.output_bytes is None
        elif unfinished:
            raise ValueError(INVALID_SAVED_RUN)
    if unknown > 1:
        raise ValueError(INVALID_SAVED_RUN)
    return CorpusRunResult(status, records, count)


def read_saved_run(
    workspace: Path,
    corpus: str,
    run_id: str,
) -> tuple[RunStatus | None, tuple[FixtureRun | None, ...]]:
    """Return saved observations, leaving missing rows unknown when no summary exists.

    The existing store still checks the source directory's disjoint identity;
    no original source file or current manifest is reopened here.
    """
    with open_run_store(workspace, corpus, run_id) as store:
        specifications = parse_evaluation_manifest(store.read_record("manifest"))
        rows = tuple(
            None
            if (payload := _optional(store, f"fixture-{index:03}")) is None
            else decode_fixture_record(payload, specification)
            for index, specification in enumerate(specifications, start=1)
        )
        summary = _optional(store, "summary")
        status = None if summary is None else _summary(summary, rows).status
    return status, rows
