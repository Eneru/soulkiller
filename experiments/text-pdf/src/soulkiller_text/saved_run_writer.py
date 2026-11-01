"""Incremental create-only persistence, sharing the runner's accepted snapshots."""

from dataclasses import asdict

from .corpus_run_result import CorpusRunResult
from .evaluation_manifest import parse_evaluation_manifest
from .fixture_record import encode_fixture_record
from .fixture_run import FixtureRun
from .loaded_fixture import LoadedFixture
from .run_store import RunStore
from .saved_json import encode_saved


def manifest_payload(fixtures: tuple[LoadedFixture, ...]) -> bytes:
    """Retain accepted reference metadata, validating its bounded restorable shape."""
    entries = []
    for fixture in fixtures:
        fields = asdict(fixture.specification)
        fields["id"] = fields.pop("fixture_id")
        entries.append(fields)
    payload = encode_saved({"schema_version": 2, "fixtures": entries})
    parse_evaluation_manifest(payload)
    return payload


class SavedRunWriter:
    """Own sequential record numbering; never retry a failed store publication."""

    def __init__(self, store: RunStore) -> None:
        """Borrow the caller's context-managed store; closing remains its responsibility."""
        self._store = store
        self._saved = 0

    def save(self, row: FixtureRun) -> None:
        """Publish a row before the next worker starts, advancing only on success."""
        self._store.write_record(f"fixture-{self._saved + 1:03}", encode_fixture_record(row))
        self._saved += 1

    def finish(self, result: CorpusRunResult) -> None:
        """Save remaining interrupted/unstarted rows and publish the final status last."""
        for row in result.fixtures[self._saved :]:
            self.save(row)
        self._store.write_record(
            "summary",
            encode_saved(
                {
                    "version": 1,
                    "status": result.status.value,
                    "output_bytes": result.output_bytes,
                }
            ),
        )
