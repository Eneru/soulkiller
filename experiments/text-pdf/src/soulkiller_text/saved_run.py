"""A complete offline extraction pass with incremental inspectable outcomes."""

from pathlib import Path
from time import monotonic

from .corpus_run_cancelled import CorpusRunCancelled
from .corpus_run_cleanup_error import CorpusRunCleanupError
from .corpus_runner import CorpusRunner
from .load_corpus import load_corpus
from .run_limits import RunLimits
from .run_status import RunStatus
from .run_store import create_run_store
from .saved_run_writer import SavedRunWriter, manifest_payload
from .worker_network_guard import has_offline_topology


def run_saved_corpus(workspace: Path, corpus: str, run_id: str) -> RunStatus:
    """Accept sources once, then checkpoint each returned row; refuse connected writes."""
    if not has_offline_topology():
        raise ValueError("offline_environment_required")
    started = monotonic()
    fixtures = load_corpus(workspace, corpus)
    metadata = manifest_payload(fixtures)
    with create_run_store(workspace, corpus, run_id) as store:
        store.write_record("manifest", metadata)
        writer = SavedRunWriter(store)
        runner = CorpusRunner(fixtures, RunLimits(), started, monotonic, writer.save)
        try:
            result = runner.run()
        except (CorpusRunCancelled, CorpusRunCleanupError) as error:
            result = error.result
        writer.finish(result)
    return result.status
