"""An immutable selected fixture's observed or unfinished execution record."""

from dataclasses import dataclass

from .corpus_fixture import CorpusFixture
from .pdf_corpus_fixture import PdfCorpusFixture
from .pdf_worker_result import PdfWorkerResult
from .run_status import RunStatus
from .worker_result import WorkerResult


@dataclass(frozen=True)
class FixtureRun:
    """Value containers do not authenticate metadata or candidate responses."""

    specification: CorpusFixture | PdfCorpusFixture
    result: WorkerResult | PdfWorkerResult | None = None
    output_bytes: int | None = 0
    unfinished_reason: RunStatus | None = None
